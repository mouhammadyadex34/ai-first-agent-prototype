from datetime import date

import pytest

from agent_first import refs
from agent_first.app import App


@pytest.fixture()
def app():
    return App(date(2026, 11, 5))


@pytest.mark.parametrize("ref, attendu", [
    ("Côte Web", 5), ("cote web", 5), ("stage développeur full stack Côte Web", 5), ("5", 5),
    ("vision par ordinateur Tarbes", 10), ("mobile La Rochelle", 11), ("data analyst Landes Analytics", 7),
])
def test_offre_resolution(app, ref, attendu):
    assert refs.offre(app, ref) == attendu


@pytest.mark.parametrize("ref", ["Aerotech Sud", "IA", "Hélios Services", "IA Bordeaux"])
def test_ambiguous_offres(app, ref):
    with pytest.raises(refs.ReferenceInvalide, match="ambigu"):
        refs.offre(app, ref)


def test_unknown_references(app):
    for bad in ("12345", "Licorne", ""):
        with pytest.raises(refs.ReferenceInvalide):
            refs.offre(app, bad)


def test_candidature_and_cv(app):
    assert refs.candidature(app, "Garonne Data") == 102
    assert refs.candidature(app, "Basque Robotique") == 103
    assert refs.cv(app, "Data") == 3 and refs.cv(app, "CV Full stack") == 1 and refs.cv(app, "IA générative") == 2


def test_retained_offers_are_no_longer_offers(app):
    app.retenir_offre(5)
    with pytest.raises(refs.ReferenceInvalide):
        refs.offre(app, "Côte Web")
    assert refs.candidature(app, "Côte Web") > 106
