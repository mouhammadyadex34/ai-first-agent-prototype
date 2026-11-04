"""Resolve what the user (and so the agent) calls things into application ids.

Version 1 of the prototype exposed ids only: with llama3.1:8b, the model invented ids (12345, 67890) instead
of looking them up first. Users never see ids in the interface; an agent should not need them either.
A reference is either an existing id or words ("Côte Web", "CV Data", "IA Bordeaux"). Exactly one match
resolves; zero or several matches return an error listing the candidates, so the agent can ask the user.
"""
import json
import re
import unicodedata

from .app import App

VIDES = set("""stage stagiaire offre offres candidature candidatures cv mon ma mes le la les l un une de du des d
chez a au aux en et pour celle celui sur dans avec the""".split())


class ReferenceInvalide(Exception):
    pass


def _mots(texte: str) -> set[str]:
    texte = "".join(c for c in unicodedata.normalize("NFD", str(texte).lower()) if unicodedata.category(c) != "Mn")
    return {m for m in re.split(r"[^a-z0-9.+#]+", texte) if m and m not in VIDES}


def _choisir(ref, lignes: list[dict], texte, libelle, nom: str) -> int:
    if isinstance(ref, int) or (isinstance(ref, str) and ref.strip().isdigit()):
        i = int(ref)
        if any(r["id"] == i for r in lignes):
            return i
        raise ReferenceInvalide(f"Aucun(e) {nom} avec l'id {i}. Cherche-le avec les outils de lecture, "
                                "ou passe le nom de l'entreprise ou du poste.")
    mots = _mots(ref)
    if not mots:
        raise ReferenceInvalide(f"Référence de {nom} vide.")
    trouves = [r for r in lignes if mots <= _mots(texte(r))]
    if len(trouves) == 1:
        return trouves[0]["id"]
    if not trouves:
        proches = [r for r in lignes if mots & _mots(texte(r))][:6]
        raise ReferenceInvalide(f"Aucun(e) {nom} ne correspond à « {ref} »."
                                + (f" Proches : {'; '.join(libelle(r) for r in proches)}." if proches else ""))
    raise ReferenceInvalide(f"« {ref} » est ambigu : {len(trouves)} {nom}s correspondent ("
                            f"{'; '.join(libelle(r) for r in trouves)}). Demande à l'utilisateur lequel, ou utilise l'id.")


def offre(app: App, ref) -> int:
    rows = [dict(r) for r in app.db.execute("SELECT * FROM offres WHERE statut = 'nouvelle'")]
    return _choisir(ref, rows, lambda r: f"{r['titre']} {r['entreprise']} {r['lieu']} {' '.join(json.loads(r['competences']))}",
                    lambda r: f"id {r['id']} : {r['titre']} — {r['entreprise']} ({r['lieu']})", "offre")


def candidature(app: App, ref) -> int:
    rows = app.lister_candidatures()
    return _choisir(ref, rows, lambda r: f"{r['entreprise']} {r['poste']} {r['lieu']}",
                    lambda r: f"id {r['id']} : {r['poste']} — {r['entreprise']} ({r['statut']})", "candidature")


def cv(app: App, ref) -> int:
    return _choisir(ref, app.lister_cv(), lambda r: r["titre"], lambda r: f"id {r['id']} : {r['titre']}", "CV")


def decrire(app: App, kind: str, id_: int) -> str:
    """Human-readable label of a resolved object, shown in the confirmation."""
    if kind == "offre":
        r = app.db.execute("SELECT titre, entreprise, lieu FROM offres WHERE id = ?", (id_,)).fetchone()
        return f"offre « {r[0]} » — {r[1]} ({r[2]})"
    if kind == "candidature":
        r = app.db.execute("SELECT poste, entreprise FROM candidatures WHERE id = ?", (id_,)).fetchone()
        return f"candidature « {r[0]} » — {r[1]}"
    r = app.db.execute("SELECT titre FROM documents WHERE id = ?", (id_,)).fetchone()
    return f"« {r[0]} »"


RESOLVEURS = {"offre": offre, "candidature": candidature, "cv": cv}
