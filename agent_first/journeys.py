"""User journeys of the graphical interface, step by step (the "classic" way to do a task).

Each step is one interaction: a click, a field to fill, a choice in a list. The counts follow the StageTrack
interface and are the reference the agent is compared with. They are an estimate made by hand, not a
measurement of real users (see README, "Limites").
"""

JOURNEYS = {
    "consulter_relances": ["Ouvrir le tableau de bord", "Lire le bloc « Relances à faire »", "Ouvrir chaque candidature concernée"],
    "retenir_offre": ["Ouvrir l'onglet Offres", "Saisir un mot-clé ou un filtre", "Ouvrir l'offre", "Cliquer « Retenir »"],
    "ignorer_offre": ["Ouvrir l'onglet Offres", "Saisir un mot-clé ou un filtre", "Ouvrir l'offre", "Cliquer « Ignorer »"],
    "associer_cv": ["Ouvrir l'onglet Candidatures", "Ouvrir la candidature", "Cliquer « Modifier »",
                    "Choisir le CV dans la liste", "Cliquer « Enregistrer »"],
    "marquer_envoyee": ["Ouvrir l'onglet Candidatures", "Rechercher la candidature", "Ouvrir la candidature",
                        "Cliquer « Je l'ai envoyée »"],
    "marquer_envoyee_date": ["Ouvrir l'onglet Candidatures", "Rechercher la candidature", "Ouvrir la candidature",
                             "Cliquer « Je l'ai envoyée »", "Modifier la date d'envoi", "Valider"],
    "planifier_relance": ["Ouvrir l'onglet Candidatures", "Rechercher la candidature", "Ouvrir la candidature",
                          "Cliquer « Modifier »", "Saisir la date de relance", "Cliquer « Enregistrer »"],
    "ajouter_note": ["Ouvrir l'onglet Candidatures", "Rechercher la candidature", "Ouvrir la candidature",
                     "Cliquer « Ajouter une note »", "Saisir la note", "Valider"],
    "rediger_relance": ["Ouvrir l'onglet Candidatures", "Rechercher la candidature", "Ouvrir la candidature",
                        "Ouvrir l'onglet Messages", "Choisir le modèle « Relance »", "Copier le message"],
    "compter_envoyees": ["Ouvrir le tableau de bord", "Lire le compteur « Envoyées »"],
}


def interactions(parcours: list[str]) -> int:
    """Number of UI interactions for a list of journeys (a task may chain several journeys)."""
    return sum(len(JOURNEYS[p]) for p in parcours)
