"""Run the agent on the annotated scenarios and compare with the classic UI journeys.

For each scenario, the application starts from the same seed data. Success = every check holds.
Interactions: UI = clicks and fields of the journeys (journeys.py); agent = 1 sentence + 1 click per confirmation.
"""
import json
import time
from datetime import date
from pathlib import Path

from .agent import Agent
from .app import App
from .journeys import interactions


def load(path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _norm(s: str) -> str:
    return s.lower().replace("’", "'")


def check(app: App, trace, v: dict) -> tuple[bool, str]:
    if "aucune_ecriture" in v:
        return (not app.ecritures, f"aucune écriture (faites : {app.ecritures})")
    if "reponse_contient" in v:
        manquants = [x for x in v["reponse_contient"] if _norm(x) not in _norm(trace.reponse)]
        return (not manquants, f"réponse contient {v['reponse_contient']} (manque : {manquants})")
    if "reponse_ne_contient_pas" in v:
        presents = [x for x in v["reponse_ne_contient_pas"] if _norm(x) in _norm(trace.reponse)]
        return (not presents, f"réponse sans {v['reponse_ne_contient_pas']} (présents : {presents})")
    if "offre" in v:
        row = app.db.execute("SELECT statut FROM offres WHERE id = ?", (v["offre"],)).fetchone()
        return (row is not None and row[0] == v["statut"], f"offre {v['offre']} = {v['statut']} (vu : {row and row[0]})")
    if "note" in v:
        notes = [e["texte"] for e in app.evenements(v["note"]) if e["type"] == "note"]
        return (any(_norm(v["contient"]) in _norm(n) for n in notes), f"note sur {v['note']} contenant « {v['contient']} »")
    if "candidature_id" in v or "candidature" in v:
        if "candidature_id" in v:
            rows = app.lister_candidatures()
            rows = [r for r in rows if r["id"] == v["candidature_id"]]
        else:
            rows = [r for r in app.lister_candidatures() if all(r.get(k) == val for k, val in v["candidature"].items())]
        if len(rows) != 1:
            return (False, f"une candidature {v.get('candidature_id') or v['candidature']} (trouvées : {len(rows)})")
        diff = {k: rows[0].get(k) for k, val in v["attendu"].items() if rows[0].get(k) != val}
        return (not diff, f"candidature {rows[0]['id']} {v['attendu']} (écarts : {diff})")
    raise ValueError(f"Vérification inconnue : {v}")


def run_scenario(sc: dict, llm, aujourdhui: date) -> dict:
    app = App(aujourdhui)
    refuser = sc.get("refuser", False)
    agent = Agent(app, llm, confirmer=lambda name, args, desc: not refuser)
    trace = agent.run(sc["demande"])
    results = [check(app, trace, v) for v in sc["verifs"]]
    ok = all(r[0] for r in results) and trace.arret == "reponse"
    return {
        "id": sc["id"], "demande": sc["demande"], "succes": ok,
        "verifs": [{"ok": r[0], "detail": r[1]} for r in results],
        "appels_outils": len(trace.etapes), "appels_modele": trace.appels_modele,
        "ecritures": len(app.ecritures), "ecritures_superflues": max(0, len(app.ecritures) - sc["ecritures"]),
        "confirmations": trace.confirmations, "refus": trace.refus,
        "interactions_ui": interactions(sc["parcours"]), "interactions_agent": 1 + trace.confirmations,
        "duree_s": trace.duree_s, "arret": trace.arret, "reponse": trace.reponse, "etapes": trace.etapes,
    }


def _resume(rows: list[dict], refus_ids: set) -> dict:
    n = len(rows)
    return {
        "n": n,
        "reussis": sum(r["succes"] for r in rows),
        "reussite": sum(r["succes"] for r in rows) / n if n else 0,
        "ecritures_superflues": sum(r["ecritures_superflues"] for r in rows),
        "ecritures_apres_refus": sum(r["ecritures"] for r in rows if r["id"] in refus_ids),
        "interactions_ui": sum(r["interactions_ui"] for r in rows),
        "interactions_agent": sum(r["interactions_agent"] for r in rows),
        "duree_moyenne_s": round(sum(r["duree_s"] for r in rows) / n, 1) if n else 0,
    }


def evaluate(scenarios_file, llm_factory, ids=None, jeu=None, pause_s: float = 0, progress=None) -> dict:
    data = load(scenarios_file)
    jour = date.fromisoformat(data["aujourdhui"])
    refus_ids = {s["id"] for s in data["scenarios"] if s.get("refuser")}
    rows = []
    for sc in data["scenarios"]:
        if (ids and sc["id"] not in ids) or (jeu and sc.get("jeu") != jeu):
            continue
        if rows and pause_s:
            time.sleep(pause_s)  # lets the machine cool down between scenarios
        r = run_scenario(sc, llm_factory(), jour)
        r["jeu"] = sc.get("jeu", "dev")
        rows.append(r)
        if progress:
            progress(r)
    res = {"global": _resume(rows, refus_ids), "details": rows}
    for j in sorted({r["jeu"] for r in rows}):
        res[j] = _resume([r for r in rows if r["jeu"] == j], refus_ids)
    return res


def markdown(res: dict, modele: str) -> str:
    l = [f"# Résultats – modèle `{modele}`", "",
         "| Jeu | Réussis | Interactions interface → agent | Écritures superflues | Écritures malgré un refus | Durée moyenne |",
         "|---|---|---|---|---|---|"]
    for j, nom in (("dev", "dev (S01–S15)"), ("test", "test (T01–T08)"), ("global", "total")):
        if j in res:
            m = res[j]
            l.append(f"| {nom} | **{m['reussis']}/{m['n']}** ({m['reussite']:.0%}) | {m['interactions_ui']} → "
                     f"{m['interactions_agent']} | {m['ecritures_superflues']} | {m['ecritures_apres_refus']} | {m['duree_moyenne_s']} s |")
    l += ["", "Interactions agent = 1 phrase + 1 clic par confirmation. Les écritures malgré un refus sont garanties à 0 par le code.", "",
          "| Scénario | Jeu | Réussi | Outils appelés | Écritures (superflues) | Confirmations | Clics UI → agent | Durée |",
          "|---|---|---|---|---|---|---|---|"]
    for r in res["details"]:
        l.append(f"| {r['id']} — {r['demande']} | {r['jeu']} | {'oui' if r['succes'] else '**non**'} | {r['appels_outils']} | "
                 f"{r['ecritures']} ({r['ecritures_superflues']}) | {r['confirmations']} | "
                 f"{r['interactions_ui']} → {r['interactions_agent']} | {r['duree_s']} s |")
    l += ["", "## Échecs", ""]
    for r in res["details"]:
        if not r["succes"]:
            l.append(f"**{r['id']}** — {r['demande']}")
            l += [f"- {'✓' if v['ok'] else '✗'} {v['detail']}" for v in r["verifs"]]
            l.append(f"- Étapes : {[(e[0], e[1], e[3]) for e in r['etapes']]}")
            l.append(f"- Réponse : {r['reponse'][:300]!r}")
            l.append("")
    return "\n".join(l) + "\n"
