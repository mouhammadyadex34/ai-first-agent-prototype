from datetime import date

import pytest

from agent_first.app import App, ErreurMetier

JOUR = date(2026, 11, 5)


@pytest.fixture()
def app():
    return App(JOUR)


def test_chercher_offres_filters(app):
    assert [o["id"] for o in app.chercher_offres(lieu="Bordeaux")] == [1, 2]
    assert [o["id"] for o in app.chercher_offres(entreprise="hélios")] == [3, 4]
    assert [o["id"] for o in app.chercher_offres(mots_cles="llm")] == [1, 2]


def test_retenir_offre_creates_candidature_once(app):
    c = app.retenir_offre(1)
    assert c["offre_id"] == 1 and c["statut"] == "a_postuler" and c["entreprise"] == "Atlantique Numérique"
    assert app.chercher_offres(entreprise="Atlantique") == []
    with pytest.raises(ErreurMetier):
        app.retenir_offre(1)
    assert app.ecritures == ["retenir_offre 1"]


def test_marquer_envoyee_sets_relance(app):
    c = app.marquer_envoyee(101, "2026-11-04")
    assert c["statut"] == "envoyee" and c["envoyee_le"] == "2026-11-04" and c["relance_le"] == "2026-11-11"
    with pytest.raises(ErreurMetier):
        app.marquer_envoyee(101)


def test_relances_a_faire_this_week(app):
    assert {c["entreprise"] for c in app.relances_a_faire()} == {"Garonne Data", "Basque Robotique"}


def test_associer_cv_rejects_non_cv(app):
    with pytest.raises(ErreurMetier):
        app.associer_cv(104, 4)
    assert app.associer_cv(104, 3)["cv_id"] == 3


def test_rediger_relance_is_read_only(app):
    msg = app.rediger_relance(102)
    assert "Garonne Data" in msg["corps"] and app.ecritures == []


def test_invalid_date(app):
    with pytest.raises(ErreurMetier):
        app.planifier_relance(102, "20/11/2026")
