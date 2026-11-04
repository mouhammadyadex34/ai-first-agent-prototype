# Des parcours utilisateurs aux agents : prototype « AI-first »

Une petite application de suivi de stages, dans l'esprit de [StageTrack](https://stagetrack.yadex.sn), où chaque **parcours de l'interface** (ouvrir l'onglet, filtrer, cliquer « Retenir », choisir le CV…) devient un **outil** qu'un agent LLM peut appeler pour exécuter une demande en langage naturel, **sous contrôle humain**.

> **Statut : prototype.** Il mesure, sur 15 demandes annotées, si un modèle local (Ollama) accomplit correctement les tâches d'une application métier, combien d'interactions il économise, et s'il respecte les refus de l'utilisateur.

Exemple du déroulé attendu (scénario S09) :

```
« Retiens l'offre full stack de Côte Web, associe mon CV Full stack et marque-la envoyée aujourd'hui. »

  [lecture]  chercher_offres(entreprise="Côte Web")         → offre 5
  [écriture] retenir_offre(offre_id=5)                      ⚠ confirmé par l'utilisateur
  [lecture]  lister_cv()                                    → CV Full stack = 1
  [écriture] associer_cv(candidature_id=107, cv_id=1)       ⚠ confirmé
  [écriture] marquer_envoyee(candidature_id=107)            ⚠ confirmé
Agent : C'est fait : candidature Côte Web créée, CV Full stack associé, envoi noté aujourd'hui (relance le 12/11).

Interface classique : 13 interactions — avec l'agent : 1 phrase + 3 confirmations.
```

## L'idée

Une application « AI-first » ne remplace pas son interface par un chatbot : elle expose **les mêmes services** que l'interface, avec le même contrôle et les mêmes règles métier, à un agent qui agit pour l'utilisateur.

- **Une seule implémentation.** Les outils de l'agent appellent les mêmes services que les boutons (`agent_first/app.py`). Une règle métier, par exemple « on ne marque pas deux fois une candidature envoyée », s'applique de la même façon aux deux.
- **Les parcours deviennent des outils.** Chaque outil est rattaché au parcours de l'interface qu'il remplace (`journeys.py`, `tools.py`). On peut ainsi comparer l'effort humain : clics et saisies d'un côté, phrase et confirmations de l'autre.
- **Lecture libre, écriture confirmée.** Chaque outil est marqué `lecture` ou `ecriture`. La boucle de l'agent (`agent.py`) garantit **par le code**, et non par le prompt :
  - qu'aucune écriture ne s'exécute sans confirmation humaine ;
  - qu'une action refusée n'est jamais reproposée ;
  - que les outils inconnus et les arguments invalides sont renvoyés au modèle comme des erreurs ;
  - que la boucle s'arrête après 12 appels au modèle.
- **Erreurs métier rendues au modèle.** Une erreur comme « l'offre 1 est déjà retenue » revient à l'agent sous forme de données, et il peut se corriger.

## Évaluation

`evaluation/scenarios.json` contient **15 demandes** écrites à la main, chacune avec l'**état attendu** de l'application après le passage de l'agent :
- des tâches simples ;
- des tâches enchaînées, jusqu'à 3 écritures ;
- des questions sans écriture ;
- 2 refus de l'utilisateur ;
- 1 demande ambiguë, à laquelle l'agent doit répondre par une question.

Chaque scénario repart des mêmes données fictives (`data/seed.json`).

Mesures relevées pour chaque scénario :
- **la réussite**, c'est-à-dire que toutes les vérifications d'état et de réponse passent ;
- **les écritures superflues**, faites alors que personne ne les a demandées ;
- **les écritures malgré un refus**, garanties à 0 par le code ;
- **les interactions**, celles de l'interface face à celles de l'agent ;
- **la durée**.

Un test vérifie que les annotations sont cohérentes avec les données : la bonne séquence d'appels satisfait toutes les vérifications.

```bash
python -m agent_first evaluer --modele qwen2.5:7b      # écrit evaluation/resultats_qwen2.5_7b.md
```

## Résultats

*Mesure en cours avec `qwen2.5:7b` sur un MacBook Air : les chiffres et les échecs analysés seront ajoutés ici, tels que mesurés.*

## Limites

- **Le nombre d'interactions de l'interface** est compté à la main d'après l'interface de StageTrack, et non mesuré sur de vrais utilisateurs.
- **15 scénarios et des données fictives** : c'est un banc d'essai, pas une étude d'usage. Le taux de réussite dépend fortement du modèle.
- **La confirmation se fait action par action.** Pour une tâche de 10 écritures, une confirmation groupée sur un plan d'actions serait plus pratique. C'est une piste, pas encore implémentée.
- **Agent à un seul tour.** Après une question de l'agent dans un cas ambigu, la conversation ne continue pas.

## Lancer le prototype

Aucune dépendance Python : bibliothèque standard uniquement, et pytest pour les tests.

```bash
brew install ollama && brew services start ollama && ollama pull qwen2.5:7b
python -m agent_first parcours                                   # les parcours de l'interface
python -m agent_first demander "Quelles candidatures dois-je relancer cette semaine ?"
python -m agent_first demander "Retiens les deux offres d'IA à Bordeaux."   # demande les confirmations
python -m agent_first evaluer --modele qwen2.5:7b
pip install pytest && pytest                                     # 15 tests, sans modèle (modèle scripté)
```

## Organisation

```
agent_first/
  app.py          services de l'application (SQLite), utilisés par l'interface et par l'agent
  journeys.py     parcours de l'interface, étape par étape
  tools.py        services exposés comme outils (schéma JSON, lecture/écriture, parcours remplacé)
  agent.py        boucle de l'agent, confirmation humaine, garde-fous
  llm.py          Ollama (local) et modèle scripté pour les tests
  evaluation.py   exécution des scénarios et métriques
data/seed.json    données fictives
evaluation/       scénarios annotés et résultats
```

## Suites possibles

- Plan d'actions confirmé en une fois, puis exécuté, avec un retour arrière si une étape échoue.
- Générer les outils automatiquement à partir du schéma OpenAPI d'une application existante (par exemple l'API REST de StageTrack).
- Comparer plusieurs modèles (taille, coût, énergie) sur le même banc d'essai.

---

Ameth YADE, Master 2 Informatique (parcours SIGLIS), Université de Pau et des Pays de l'Adour.
