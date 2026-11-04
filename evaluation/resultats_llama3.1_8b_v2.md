# Résultats – version 2 (outils par référence) – modèle `llama3.1:8b`

| Jeu | Réussis | Interactions interface → agent | Écritures superflues | Écritures malgré un refus | Durée moyenne |
|---|---|---|---|---|---|
| dev (S01–S15) | **10/15** (67%) | 97 → 25 | 0 | 0 | 5.8 s |
| test (T01–T08) | **4/8** (50%) | 40 → 14 | 0 | 0 | 6.5 s |
| total | **14/23** (61%) | 137 → 39 | 0 | 0 | 6.0 s |

Interactions agent = 1 phrase + 1 clic par confirmation. Les écritures malgré un refus sont garanties à 0 par le code.

| Scénario | Jeu | Réussi | Outils appelés | Écritures (superflues) | Confirmations | Clics UI → agent | Durée |
|---|---|---|---|---|---|---|---|
| S01 — Retiens l'offre de stage IA générative chez Atlantique Numérique et associe-lui mon CV IA générative. | dev | **non** | 2 | 0 (0) | 0 | 9 → 1 | 8.69 s |
| S02 — Ignore l'offre de technicien support chez Hélios Services. | dev | oui | 1 | 1 (0) | 1 | 4 → 2 | 2.36 s |
| S03 — J'ai envoyé hier ma candidature chez Pyrène Logiciels, note-la comme envoyée. | dev | oui | 1 | 1 (0) | 1 | 6 → 2 | 5.06 s |
| S04 — Quelles candidatures dois-je relancer cette semaine ? | dev | oui | 1 | 0 (0) | 0 | 3 → 1 | 5.44 s |
| S05 — Décale la relance de ma candidature chez Garonne Data au 20 novembre. | dev | oui | 1 | 1 (0) | 1 | 6 → 2 | 5.11 s |
| S06 — Retiens les deux offres d'IA à Bordeaux. | dev | **non** | 2 | 0 (0) | 0 | 8 → 1 | 5.55 s |
| S07 — Ajoute une note à ma candidature chez Basque Robotique : entretien téléphonique prévu jeudi prochain. | dev | oui | 1 | 1 (0) | 1 | 6 → 2 | 5.5 s |
| S08 — Prépare-moi un message de relance pour Garonne Data. | dev | oui | 1 | 0 (0) | 0 | 6 → 1 | 4.37 s |
| S09 — Retiens l'offre full stack de Côte Web, associe mon CV Full stack et marque-la envoyée aujourd'hui. | dev | oui | 3 | 3 (0) | 3 | 13 → 4 | 11.02 s |
| S10 — Retiens l'offre de data engineer chez Garonne Data. | dev | oui | 1 | 0 (0) | 1 | 4 → 2 | 2.74 s |
| S11 — Marque comme envoyée ma candidature chez Pyrène Logiciels. | dev | oui | 1 | 0 (0) | 1 | 4 → 2 | 4.5 s |
| S12 — Retiens l'offre d'Aerotech Sud. | dev | oui | 1 | 0 (0) | 0 | 4 → 1 | 8.17 s |
| S13 — Associe mon CV Data à toutes mes candidatures à postuler qui n'ont pas encore de CV. | dev | **non** | 1 | 0 (0) | 0 | 10 → 1 | 6.49 s |
| S14 — Combien de candidatures ai-je envoyées ? | dev | **non** | 1 | 0 (0) | 0 | 2 → 1 | 5.4 s |
| S15 — Ignore les offres d'Hélios Services et retiens celle d'Adour Cloud. | dev | **non** | 2 | 1 (0) | 1 | 12 → 2 | 6.74 s |
| T01 — Mets de côté l'offre de développeur mobile à La Rochelle. | test | **non** | 1 | 1 (0) | 1 | 4 → 2 | 4.89 s |
| T02 — Je ne suis pas intéressé par le stage data analyst de Landes Analytics, enlève-le. | test | oui | 1 | 1 (0) | 1 | 4 → 2 | 4.56 s |
| T03 — Ma candidature chez Navarre Soft est partie ce matin. | test | oui | 1 | 1 (0) | 1 | 4 → 2 | 6.17 s |
| T04 — Avec quel CV ai-je postulé chez Basque Robotique ? | test | **non** | 1 | 0 (0) | 0 | 3 → 1 | 6.05 s |
| T05 — Repousse d'une semaine la relance de ma candidature chez Basque Robotique. | test | **non** | 1 | 1 (0) | 1 | 6 → 2 | 6.6 s |
| T06 — Retiens l'offre de vision par ordinateur à Tarbes et mets-lui mon CV IA générative. | test | **non** | 1 | 1 (0) | 1 | 9 → 2 | 7.69 s |
| T07 — Note dans ma candidature chez Landes Tech que le recruteur s'appelle M. Duval. | test | oui | 1 | 1 (0) | 1 | 6 → 2 | 5.45 s |
| T08 — Retiens l'offre en IA. | test | oui | 1 | 0 (0) | 0 | 4 → 1 | 10.59 s |

## Échecs

**S01** — Retiens l'offre de stage IA générative chez Atlantique Numérique et associe-lui mon CV IA générative.
- ✗ une candidature {'offre_id': 1} (trouvées : 0)
- ✗ offre 1 = retenue (vu : nouvelle)
- Étapes : [('retenir_offre', {'offre': 'Atlantique Numérique, IA générative, lieu'}, 'référence invalide'), ('associer_cv', {'candidature': 'Atlantique Numérique, IA générative', 'cv': 'IA générative'}, 'référence invalide')]
- Réponse : "L'utilisateur doit préciser l'offre et le CV correspondants."

**S06** — Retiens les deux offres d'IA à Bordeaux.
- ✗ une candidature {'offre_id': 1} (trouvées : 0)
- ✗ une candidature {'offre_id': 2} (trouvées : 0)
- Étapes : [('retenir_offre', {'offre': 'IA, Bordeaux'}, 'référence invalide'), ('retenir_offre', {'offre': 'IA, Bordeaux'}, 'référence invalide')]
- Réponse : "L'utilisateur doit préciser laquelle des deux offres il souhaite retenir."

**S13** — Associe mon CV Data à toutes mes candidatures à postuler qui n'ont pas encore de CV.
- ✗ candidature 104 {'cv_id': 3} (écarts : {'cv_id': None})
- ✗ candidature 105 {'cv_id': 3} (écarts : {'cv_id': None})
- ✓ candidature 101 {'cv_id': 1} (écarts : {})
- Étapes : [('associer_cv', {'candidature': 'toutes les candidatures à postuler sans CV', 'cv': 'Data'}, 'référence invalide')]
- Réponse : "Je suis désolé, mais il semble que vous n'ayez aucune candidature à postuler sans CV. Voulez-vous préciser les candidatures que vous souhaitez associer à votre CV ?"

**S14** — Combien de candidatures ai-je envoyées ?
- ✓ aucune écriture (faites : [])
- ✗ réponse contient ['3'] (manque : ['3'])
- Étapes : [('lister_candidatures', {'entreprise': 'entreprise', 'statut': 'envoyee'}, 'ok')]
- Réponse : "Vous n'avez pas envoyé de candidatures."

**S15** — Ignore les offres d'Hélios Services et retiens celle d'Adour Cloud.
- ✗ offre 3 = ignoree (vu : nouvelle)
- ✗ offre 4 = ignoree (vu : nouvelle)
- ✓ candidature 107 {'statut': 'a_postuler'} (écarts : {})
- Étapes : [('ignorer_offre', {'offre': 'Hélios Services'}, 'référence invalide'), ('retenir_offre', {'offre': 'Adour Cloud'}, 'ok')]
- Réponse : "L'offre d'Adour Cloud a été retenue."

**T01** — Mets de côté l'offre de développeur mobile à La Rochelle.
- ✗ une candidature {'offre_id': 11} (trouvées : 0)
- Étapes : [('ignorer_offre', {'offre': 'développeur mobile, La Rochelle'}, 'ok')]
- Réponse : "L'offre de développeur mobile à La Rochelle a été mise de côté."

**T04** — Avec quel CV ai-je postulé chez Basque Robotique ?
- ✓ aucune écriture (faites : [])
- ✗ réponse contient ['IA générative'] (manque : ['IA générative'])
- Étapes : [('lister_candidatures', {'entreprise': 'Basque Robotique', 'statut': 'a_postuler'}, 'ok')]
- Réponse : "Je n'ai trouvé aucun CV associé à une candidature postulée chez Basque Robotique. Voulez-vous préciser la candidature ?"

**T05** — Repousse d'une semaine la relance de ma candidature chez Basque Robotique.
- ✗ candidature 103 {'relance_le': '2026-11-13'} (écarts : {'relance_le': '2026-11-12'})
- Étapes : [('planifier_relance', {'candidature': 'Basque Robotique', 'jour': '2026-11-12'}, 'ok')]
- Réponse : 'La relance de votre candidature chez Basque Robotique a été planifiée pour le 2026-11-12.'

**T06** — Retiens l'offre de vision par ordinateur à Tarbes et mets-lui mon CV IA générative.
- ✗ candidature 107 {'statut': 'a_postuler', 'cv_id': 2} (écarts : {'cv_id': None})
- Étapes : [('retenir_offre', {'offre': 'vision par ordinateur à Tarbes'}, 'ok')]
- Réponse : 'J\'ai retenu l\'offre de vision par ordinateur à Tarbes. Je vais maintenant envoyer ton CV IA générative pour cette offre.\n\n{"name": "envoyer_cv", "parameters": {"cv": "IA générative", "offre_id": 10}}'

