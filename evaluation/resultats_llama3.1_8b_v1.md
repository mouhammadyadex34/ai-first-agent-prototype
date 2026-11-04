# Résultats – version 1 (outils par identifiant) – modèle `llama3.1:8b`

- Scénarios réussis : **0/4** (0%)
- Interactions : **22** dans l'interface classique contre **7** avec l'agent (1 phrase + 1 clic par confirmation)
- Écritures superflues (non demandées) : **0**
- Écritures malgré un refus de l'utilisateur : **0** (garanti à 0 par le code)
- Durée moyenne par demande : 6.4 s

| Scénario | Réussi | Outils appelés | Écritures (superflues) | Confirmations | Clics UI → agent | Durée |
|---|---|---|---|---|---|---|
| S01 — Retiens l'offre de stage IA générative chez Atlantique Numérique et associe-lui mon CV IA générative. | **non** | 2 | 0 (0) | 2 | 9 → 3 | 12.05 s |
| S02 — Ignore l'offre de technicien support chez Hélios Services. | **non** | 1 | 0 (0) | 1 | 4 → 2 | 4.77 s |
| S04 — Quelles candidatures dois-je relancer cette semaine ? | **non** | 1 | 0 (0) | 0 | 3 → 1 | 4.22 s |
| S08 — Prépare-moi un message de relance pour Garonne Data. | **non** | 1 | 0 (0) | 0 | 6 → 1 | 4.68 s |

## Échecs

**S01** — Retiens l'offre de stage IA générative chez Atlantique Numérique et associe-lui mon CV IA générative.
- ✗ une candidature {'offre_id': 1} (trouvées : 0)
- ✗ offre 1 = retenue (vu : nouvelle)
- Étapes : [('retenir_offre', {'offre_id': 12345}, 'erreur'), ('associer_cv', {'candidature_id': 12345, 'cv_id': 67890}, 'erreur')]
- Réponse : "Pouvez-vous me donner l'identifiant de l'offre de stage IA générative chez Atlantique Numérique ?"

**S02** — Ignore l'offre de technicien support chez Hélios Services.
- ✗ offre 3 = ignoree (vu : nouvelle)
- ✓ offre 4 = nouvelle (vu : nouvelle)
- Étapes : [('ignorer_offre', {'offre_id': 12345}, 'erreur')]
- Réponse : "Je ne peux pas ignorer l'offre car elle n'existe pas dans la base de données. \n\nPouvez-vous me donner l'ID de l'offre que vous souhaitez ignorer ?"

**S04** — Quelles candidatures dois-je relancer cette semaine ?
- ✓ aucune écriture (faites : [])
- ✗ réponse contient ['Garonne Data', 'Basque Robotique'] (manque : ['Garonne Data', 'Basque Robotique'])
- ✓ réponse sans ['Landes Tech'] (présents : [])
- Étapes : [('relances_a_faire', {'jusqu_au': '2026-11-11'}, 'ok')]
- Réponse : 'Vous devez relancer les candidatures avec les id 102 et 103.'

**S08** — Prépare-moi un message de relance pour Garonne Data.
- ✓ aucune écriture (faites : [])
- ✗ réponse contient ['Garonne Data'] (manque : ['Garonne Data'])
- Étapes : [('rediger_relance', {'candidature_id': 'null'}, 'arguments invalides')]
- Réponse : "Je ne connais pas l'identifiant de la candidature. Pouvez-vous me donner l'identifiant de la candidature que vous souhaitez relancer ?"

