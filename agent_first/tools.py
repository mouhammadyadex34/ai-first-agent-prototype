"""The application's services exposed as tools for the agent.

Every tool says whether it only reads ("lecture") or changes data ("ecriture"). Writes go through a
human confirmation gate in the agent loop: the model can propose them, never perform them alone.
"""
from dataclasses import dataclass

from .app import App, ErreurMetier


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict  # JSON schema of the arguments
    effet: str        # "lecture" or "ecriture"
    parcours: str     # UI journey this tool replaces (see journeys.py)

    def schema(self) -> dict:
        return {"type": "function", "function": {"name": self.name, "description": self.description,
                                                 "parameters": self.parameters}}


def _obj(props: dict, required=()):
    return {"type": "object", "properties": props, "required": list(required)}


ID = {"type": "integer"}
TXT = {"type": "string"}

TOOLS = [
    Tool("chercher_offres", "Cherche les offres de stage nouvelles (non traitées). Filtres optionnels : mots-clés du titre ou "
         "des compétences, lieu, entreprise. Renvoie les offres avec leur id.",
         _obj({"mots_cles": TXT, "lieu": TXT, "entreprise": TXT}), "lecture", "retenir_offre"),
    Tool("lister_candidatures", "Liste les candidatures de l'utilisateur avec leur id, statut (a_postuler, envoyee, relancee), "
         "CV associé, date d'envoi et date de relance. Filtres optionnels : statut, entreprise.",
         _obj({"statut": TXT, "entreprise": TXT}), "lecture", "marquer_envoyee"),
    Tool("lister_cv", "Liste les CV de l'utilisateur avec leur id et leur titre.", _obj({}), "lecture", "associer_cv"),
    Tool("relances_a_faire", "Candidatures envoyées dont la relance est due au plus tard à la date donnée "
         "(par défaut : fin de la semaine en cours).", _obj({"jusqu_au": {"type": "string", "description": "AAAA-MM-JJ"}}),
         "lecture", "consulter_relances"),
    Tool("rediger_relance", "Rédige un brouillon de message de relance pour une candidature envoyée. N'envoie rien.",
         _obj({"candidature_id": ID}, ["candidature_id"]), "lecture", "rediger_relance"),
    Tool("retenir_offre", "Retient une offre : crée une candidature « à postuler » liée à cette offre. Renvoie la candidature créée.",
         _obj({"offre_id": ID}, ["offre_id"]), "ecriture", "retenir_offre"),
    Tool("ignorer_offre", "Ignore une offre : elle disparaît des offres nouvelles.", _obj({"offre_id": ID}, ["offre_id"]),
         "ecriture", "ignorer_offre"),
    Tool("associer_cv", "Associe un CV à une candidature.", _obj({"candidature_id": ID, "cv_id": ID}, ["candidature_id", "cv_id"]),
         "ecriture", "associer_cv"),
    Tool("marquer_envoyee", "Marque une candidature « à postuler » comme envoyée, à la date donnée (par défaut aujourd'hui). "
         "La relance est planifiée 7 jours plus tard.",
         _obj({"candidature_id": ID, "jour": {"type": "string", "description": "AAAA-MM-JJ"}}, ["candidature_id"]),
         "ecriture", "marquer_envoyee"),
    Tool("planifier_relance", "Change la date de relance d'une candidature.",
         _obj({"candidature_id": ID, "jour": {"type": "string", "description": "AAAA-MM-JJ"}}, ["candidature_id", "jour"]),
         "ecriture", "planifier_relance"),
    Tool("ajouter_note", "Ajoute une note datée à une candidature.", _obj({"candidature_id": ID, "texte": TXT},
                                                                          ["candidature_id", "texte"]),
         "ecriture", "ajouter_note"),
]
BY_NAME = {t.name: t for t in TOOLS}


class ArgumentsInvalides(Exception):
    pass


def check_arguments(tool: Tool, args: dict) -> dict:
    """Keep known arguments, check required ones and types (models sometimes send ids as strings)."""
    if not isinstance(args, dict):
        raise ArgumentsInvalides("Les arguments doivent être un objet JSON.")
    props, out = tool.parameters["properties"], {}
    for name in tool.parameters["required"]:
        if name not in args or args[name] in (None, ""):
            raise ArgumentsInvalides(f"Argument obligatoire manquant : {name}.")
    for name, value in args.items():
        if name not in props or value in (None, ""):
            continue
        if props[name]["type"] == "integer":
            try:
                value = int(value)
            except (TypeError, ValueError):
                raise ArgumentsInvalides(f"{name} doit être un entier.")
        else:
            value = str(value)
        out[name] = value
    return out


def execute(app: App, tool: Tool, args: dict):
    """Run a tool; business errors are returned to the model as data so that it can correct itself."""
    try:
        return {"ok": True, "resultat": getattr(app, tool.name)(**args)}
    except ErreurMetier as e:
        return {"ok": False, "erreur": str(e)}
