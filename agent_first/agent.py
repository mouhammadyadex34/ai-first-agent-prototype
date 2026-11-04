"""The agent loop: the model reads with tools freely and proposes writes; a human confirms each write.

Guarantees enforced by code (not by the prompt):
  - a write tool runs only if the confirmation function returns True;
  - after a refusal, the same write is never proposed to the human again in this conversation;
  - unknown tools, invalid arguments and unresolvable references are returned to the model as errors;
  - references are resolved before the confirmation: the human confirms a named object, not an id;
  - the loop stops after `max_etapes` model calls.
"""
import json
import time
from dataclasses import dataclass, field
from typing import Callable

from .app import App
from .refs import ReferenceInvalide
from .tools import BY_NAME, TOOLS, ArgumentsInvalides, check_arguments, execute, resolve

SYSTEM = """Tu es l'assistant d'une application de suivi de candidatures de stage. Tu agis pour l'utilisateur en appelant les outils.
Nous sommes le {jour} ({jour_semaine}).
Règles :
- Désigne les offres, candidatures et CV avec les mots de l'utilisateur (entreprise, poste, lieu, titre du CV) : l'application retrouve l'élément. N'invente jamais d'identifiant.
- Fais exactement ce que l'utilisateur demande, pas plus.
- Si un outil répond qu'une référence est ambiguë ou introuvable, n'agis pas au hasard : demande à l'utilisateur de préciser.
- Les actions qui modifient des données sont confirmées par l'utilisateur dans l'application : appelle simplement l'outil. Si l'utilisateur refuse, ne réessaie pas et dis que rien n'a été fait.
- Les dates s'écrivent AAAA-MM-JJ.
- Réponds en français, brièvement. Nomme les entreprises et les postes ; ne donne jamais d'identifiant numérique à l'utilisateur."""

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


@dataclass
class Trace:
    demande: str
    etapes: list = field(default_factory=list)   # (tool, args, effet, statut, résultat abrégé)
    reponse: str = ""
    appels_modele: int = 0
    confirmations: int = 0
    refus: int = 0
    duree_s: float = 0.0
    arret: str = "reponse"  # "reponse" or "limite"


def toujours_oui(tool_name: str, args: dict, description: str = "") -> bool:
    return True


class Agent:
    def __init__(self, app: App, llm, confirmer: Callable[[str, dict, str], bool] = toujours_oui, max_etapes: int = 12):
        self.app, self.llm, self.confirmer, self.max_etapes = app, llm, confirmer, max_etapes

    def run(self, demande: str) -> Trace:
        trace, debut = Trace(demande), time.monotonic()
        jour = self.app.aujourdhui
        messages = [{"role": "system", "content": SYSTEM.format(jour=jour.isoformat(), jour_semaine=JOURS[jour.weekday()])},
                    {"role": "user", "content": demande}]
        refusees = set()
        schemas = [t.schema() for t in TOOLS]
        for _ in range(self.max_etapes):
            reply = self.llm.chat(messages, schemas)
            trace.appels_modele += 1
            if not reply.tool_calls:
                trace.reponse = reply.content.strip()
                break
            messages.append({"role": "assistant", "content": reply.content,
                             "tool_calls": [{"function": {"name": c.name, "arguments": c.arguments}} for c in reply.tool_calls]})
            for call in reply.tool_calls:
                result = self._call(call, refusees, trace)
                messages.append({"role": "tool", "tool_name": call.name,
                                 "content": json.dumps(result, ensure_ascii=False, default=str)})
        else:
            trace.arret = "limite"
        trace.duree_s = round(time.monotonic() - debut, 2)
        return trace

    def _call(self, call, refusees: set, trace: Trace) -> dict:
        tool = BY_NAME.get(call.name)
        if tool is None:
            trace.etapes.append((call.name, call.arguments, "?", "outil inconnu", ""))
            return {"ok": False, "erreur": f"Outil inconnu : {call.name}. Outils disponibles : {', '.join(BY_NAME)}."}
        try:
            args = check_arguments(tool, call.arguments)
        except ArgumentsInvalides as e:
            trace.etapes.append((tool.name, call.arguments, tool.effet, "arguments invalides", str(e)))
            return {"ok": False, "erreur": str(e)}
        try:
            service_args, description = resolve(self.app, tool, args)
        except ReferenceInvalide as e:
            trace.etapes.append((tool.name, args, tool.effet, "référence invalide", str(e)))
            return {"ok": False, "erreur": str(e)}
        if tool.effet == "ecriture":
            cle = (tool.name, json.dumps(service_args, sort_keys=True))
            if cle in refusees:
                trace.etapes.append((tool.name, args, tool.effet, "déjà refusée", ""))
                return {"ok": False, "erreur": "L'utilisateur a déjà refusé cette action. Ne la propose plus."}
            trace.confirmations += 1
            if not self.confirmer(tool.name, service_args, description):
                refusees.add(cle)
                trace.refus += 1
                trace.etapes.append((tool.name, args, tool.effet, "refusée", description))
                return {"ok": False, "erreur": "Action refusée par l'utilisateur. Rien n'a été modifié. Ne réessaie pas."}
        result = execute(self.app, tool, service_args)
        trace.etapes.append((tool.name, args, tool.effet, "ok" if result["ok"] else "erreur",
                             json.dumps(result, ensure_ascii=False, default=str)[:160]))
        return result
