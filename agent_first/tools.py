"""The application's services exposed as tools for the agent.

Every tool says whether it only reads ("lecture") or changes data ("ecriture"). Writes go through a
human confirmation gate in the agent loop: the model can propose them, never perform them alone.

Since version 2, tools that act on an object take a *reference* (the words the user uses, or an id),
resolved by refs.py before the confirmation, so the human confirms a named object, not a number.
"""
from dataclasses import dataclass, field

from . import refs
from .app import App, ErreurMetier


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict  # JSON schema of the arguments
    effet: str        # "lecture" or "ecriture"
    parcours: str     # UI journey this tool replaces (see journeys.py)
    references: dict = field(default_factory=dict)  # argument -> (kind, service argument), e.g. "offre" -> ("offre", "offre_id")

    def schema(self) -> dict:
        return {"type": "function", "function": {"name": self.name, "description": self.description,
                                                 "parameters": self.parameters}}


def _obj(props: dict, required=()):
    return {"type": "object", "properties": props, "required": list(required)}


TXT = {"type": "string"}
JOUR = {"type": "string", "description": "AAAA-MM-JJ"}
REF_OFFRE = {"type": "string", "description": "L'offre telle que l'utilisateur la désigne (entreprise, mots du titre, lieu) ou son id"}
REF_CAND = {"type": "string", "description": "La candidature telle que l'utilisateur la désigne (entreprise, poste) ou son id"}
REF_CV = {"type": "string", "description": "Le CV tel que l'utilisateur le désigne (ex. « Data », « Full stack ») ou son id"}

TOOLS = [
    Tool("chercher_offres", "Cherche les offres de stage nouvelles (non traitées). Filtres optionnels : mots-clés du titre ou "
         "des compétences, lieu, entreprise.", _obj({"mots_cles": TXT, "lieu": TXT, "entreprise": TXT}), "lecture", "retenir_offre"),
    Tool("lister_candidatures", "Liste les candidatures : entreprise, poste, statut (a_postuler, envoyee, relancee), CV associé "
         "(cv_id, null si aucun), dates d'envoi et de relance. Filtres optionnels : statut, entreprise.",
         _obj({"statut": TXT, "entreprise": TXT}), "lecture", "marquer_envoyee"),
    Tool("lister_cv", "Liste les CV de l'utilisateur.", _obj({}), "lecture", "associer_cv"),
    Tool("relances_a_faire", "Candidatures envoyées dont la relance est due au plus tard à la date donnée "
         "(par défaut : fin de la semaine en cours).", _obj({"jusqu_au": JOUR}), "lecture", "consulter_relances"),
    Tool("rediger_relance", "Rédige un brouillon de message de relance pour une candidature envoyée. N'envoie rien.",
         _obj({"candidature": REF_CAND}, ["candidature"]), "lecture", "rediger_relance",
         {"candidature": ("candidature", "candidature_id")}),
    Tool("retenir_offre", "Retient une offre : crée une candidature « à postuler » pour cette offre.",
         _obj({"offre": REF_OFFRE}, ["offre"]), "ecriture", "retenir_offre", {"offre": ("offre", "offre_id")}),
    Tool("ignorer_offre", "Ignore une offre : elle disparaît des offres nouvelles.",
         _obj({"offre": REF_OFFRE}, ["offre"]), "ecriture", "ignorer_offre", {"offre": ("offre", "offre_id")}),
    Tool("associer_cv", "Associe un CV à une candidature.", _obj({"candidature": REF_CAND, "cv": REF_CV}, ["candidature", "cv"]),
         "ecriture", "associer_cv", {"candidature": ("candidature", "candidature_id"), "cv": ("cv", "cv_id")}),
    Tool("marquer_envoyee", "Marque une candidature « à postuler » comme envoyée, à la date donnée (par défaut aujourd'hui). "
         "La relance est planifiée 7 jours plus tard.", _obj({"candidature": REF_CAND, "jour": JOUR}, ["candidature"]),
         "ecriture", "marquer_envoyee", {"candidature": ("candidature", "candidature_id")}),
    Tool("planifier_relance", "Change la date de relance d'une candidature.",
         _obj({"candidature": REF_CAND, "jour": JOUR}, ["candidature", "jour"]),
         "ecriture", "planifier_relance", {"candidature": ("candidature", "candidature_id")}),
    Tool("ajouter_note", "Ajoute une note datée à une candidature.", _obj({"candidature": REF_CAND, "texte": TXT},
                                                                          ["candidature", "texte"]),
         "ecriture", "ajouter_note", {"candidature": ("candidature", "candidature_id")}),
]
BY_NAME = {t.name: t for t in TOOLS}


class ArgumentsInvalides(Exception):
    pass


def check_arguments(tool: Tool, args: dict) -> dict:
    """Keep known arguments and check required ones. Models sometimes send "null" or numbers as strings."""
    if not isinstance(args, dict):
        raise ArgumentsInvalides("Les arguments doivent être un objet JSON.")
    props, out = tool.parameters["properties"], {}
    for name, value in args.items():
        if name in props and value not in (None, "") and str(value).strip().lower() not in ("null", "none"):
            out[name] = str(value).strip()
    missing = [n for n in tool.parameters["required"] if n not in out]
    if missing:
        raise ArgumentsInvalides(f"Argument obligatoire manquant : {', '.join(missing)}.")
    return out


def resolve(app: App, tool: Tool, args: dict) -> tuple[dict, str]:
    """References -> service arguments (ids), plus a human description of the action for the confirmation."""
    service_args, labels = {}, []
    for name, value in args.items():
        if name in tool.references:
            kind, target = tool.references[name]
            id_ = refs.RESOLVEURS[kind](app, value)
            service_args[target] = id_
            labels.append(refs.decrire(app, kind, id_))
        else:
            service_args[name] = value
    extra = [f"{k} = {v}" for k, v in args.items() if k not in tool.references]
    return service_args, f"{tool.name} : {', '.join(labels + extra)}"


def execute(app: App, tool: Tool, service_args: dict):
    """Run a tool; business errors are returned to the model as data so that it can correct itself."""
    try:
        return {"ok": True, "resultat": getattr(app, tool.name)(**service_args)}
    except ErreurMetier as e:
        return {"ok": False, "erreur": str(e)}
