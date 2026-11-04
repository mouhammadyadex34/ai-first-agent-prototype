from datetime import date
from pathlib import Path

from agent_first.agent import Agent
from agent_first.app import App
from agent_first.evaluation import check, load, run_scenario
from agent_first.llm import Reply, ScriptedChat, ToolCall
from agent_first.tools import BY_NAME, TOOLS

JOUR = date(2026, 11, 5)
SCENARIOS = Path(__file__).resolve().parent.parent / "evaluation" / "scenarios.json"


def test_every_tool_maps_to_a_service_and_a_journey():
    from agent_first.journeys import JOURNEYS
    for t in TOOLS:
        assert hasattr(App, t.name) and t.parcours in JOURNEYS and t.effet in ("lecture", "ecriture")


def test_write_is_executed_only_after_confirmation():
    app = App(JOUR)
    asked = []
    llm = ScriptedChat([Reply(tool_calls=[ToolCall("retenir_offre", {"offre_id": "5"})]), Reply("C'est fait.")])
    trace = Agent(app, llm, confirmer=lambda n, a: asked.append((n, a)) or True).run("Retiens Côte Web")
    assert asked == [("retenir_offre", {"offre_id": 5})]  # "5" converted to int before confirmation
    assert app.ecritures == ["retenir_offre 5"] and trace.reponse == "C'est fait."


def test_refusal_blocks_the_write_and_its_retry():
    app = App(JOUR)
    call = ToolCall("marquer_envoyee", {"candidature_id": 101})
    llm = ScriptedChat([Reply(tool_calls=[call]), Reply(tool_calls=[call]), Reply("Rien n'a été fait.")])
    asked = []
    trace = Agent(app, llm, confirmer=lambda n, a: asked.append(n) and False).run("Marque Pyrène envoyée")
    assert app.ecritures == []
    assert len(asked) == 1 and trace.refus == 1  # the second identical proposal never reaches the human
    assert trace.etapes[1][3] == "déjà refusée"


def test_reads_need_no_confirmation_and_errors_go_back_to_the_model():
    app = App(JOUR)
    llm = ScriptedChat([
        Reply(tool_calls=[ToolCall("lister_cv", {}), ToolCall("outil_fantome", {}),
                          ToolCall("associer_cv", {"candidature_id": 104}), ToolCall("retenir_offre", {"offre_id": 999})]),
        Reply("Terminé."),
    ])
    trace = Agent(app, llm, confirmer=lambda n, a: True).run("…")
    statuts = [e[3] for e in trace.etapes]
    assert statuts == ["ok", "outil inconnu", "arguments invalides", "erreur"]
    assert trace.confirmations == 1 and app.ecritures == []
    tool_messages = [m for m in llm.received[1] if m["role"] == "tool"]
    assert len(tool_messages) == 4 and "Outil inconnu" in tool_messages[1]["content"]


def test_step_limit():
    app = App(JOUR)
    llm = ScriptedChat([Reply(tool_calls=[ToolCall("lister_cv", {})])] * 20)
    trace = Agent(app, llm, max_etapes=3).run("boucle")
    assert trace.arret == "limite" and trace.appels_modele == 3


# The right sequence of service calls for each scenario. If the annotations are coherent with the data,
# applying it must satisfy every check: this guards the evaluation set itself.
ORACLE = {
    "S01": [("retenir_offre", {"offre_id": 1}), ("associer_cv", {"candidature_id": None, "cv_id": 2})],
    "S02": [("ignorer_offre", {"offre_id": 3})],
    "S03": [("marquer_envoyee", {"candidature_id": 101, "jour": "2026-11-04"})],
    "S04": [], "S08": [], "S10": [], "S11": [], "S12": [], "S14": [],
    "S05": [("planifier_relance", {"candidature_id": 102, "jour": "2026-11-20"})],
    "S06": [("retenir_offre", {"offre_id": 1}), ("retenir_offre", {"offre_id": 2})],
    "S07": [("ajouter_note", {"candidature_id": 103, "texte": "Entretien téléphonique prévu jeudi prochain"})],
    "S09": [("retenir_offre", {"offre_id": 5}), ("associer_cv", {"candidature_id": None, "cv_id": 1}),
            ("marquer_envoyee", {"candidature_id": None})],
    "S13": [("associer_cv", {"candidature_id": 104, "cv_id": 3}), ("associer_cv", {"candidature_id": 105, "cv_id": 3})],
    "S15": [("ignorer_offre", {"offre_id": 3}), ("ignorer_offre", {"offre_id": 4}), ("retenir_offre", {"offre_id": 6})],
}
ORACLE_ANSWERS = {"S04": "Garonne Data (relance due le 3) et Basque Robotique (le 6).",
                  "S08": "Voici un brouillon de relance pour Garonne Data.", "S14": "Tu as envoyé 3 candidatures."}


def test_annotations_are_satisfiable():
    data = load(SCENARIOS)
    assert len(data["scenarios"]) == 15
    for sc in data["scenarios"]:
        app, created = App(JOUR), None
        for name, args in ORACLE[sc["id"]]:
            args = {k: (created if v is None else v) for k, v in args.items()}
            out = getattr(app, name)(**args)
            if name == "retenir_offre":
                created = out["id"]
        trace = type("T", (), {"reponse": ORACLE_ANSWERS.get(sc["id"], "")})()
        for v in sc["verifs"]:
            ok, detail = check(app, trace, v)
            assert ok, (sc["id"], detail)
        assert len(app.ecritures) == sc["ecritures"], sc["id"]


def test_run_scenario_with_scripted_model():
    sc = next(s for s in load(SCENARIOS)["scenarios"] if s["id"] == "S02")
    llm = ScriptedChat([Reply(tool_calls=[ToolCall("chercher_offres", {"entreprise": "Hélios"})]),
                        Reply(tool_calls=[ToolCall("ignorer_offre", {"offre_id": 3})]),
                        Reply("J'ai ignoré l'offre de technicien support.")])
    r = run_scenario(sc, llm, JOUR)
    assert r["succes"] and r["ecritures_superflues"] == 0 and r["interactions_ui"] == 4 and r["interactions_agent"] == 2


def test_tool_schemas_are_valid_for_ollama():
    for t in TOOLS:
        s = t.schema()
        assert s["type"] == "function" and s["function"]["parameters"]["type"] == "object"
        assert set(s["function"]["parameters"]["required"]) <= set(s["function"]["parameters"]["properties"])
    assert BY_NAME["rediger_relance"].effet == "lecture"
