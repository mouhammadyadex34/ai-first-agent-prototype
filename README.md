# Des parcours utilisateurs aux agents : prototype « AI-first »

Une petite application de suivi de stages, dans l'esprit de [StageTrack](https://stagetrack.yadex.sn), où chaque **parcours de l'interface** (ouvrir l'onglet, filtrer, cliquer « Retenir », choisir le CV…) devient un **outil** qu'un agent LLM peut appeler pour exécuter une demande en langage naturel, **sous contrôle humain**.

> **Statut : prototype.** Il mesure, sur 23 demandes annotées, si un modèle local (Ollama) accomplit correctement les tâches d'une application métier, combien d'interactions il économise, et s'il respecte les refus de l'utilisateur.

Exemple du déroulé attendu (scénario S09) :

```
« Retiens l'offre full stack de Côte Web, associe mon CV Full stack et marque-la envoyée aujourd'hui. »

  [écriture] retenir_offre(offre="full stack Côte Web")
             ⚠ « retenir_offre : offre « Stage développeur full stack React / Django » — Côte Web (Biarritz) » ? oui
  [écriture] associer_cv(candidature="Côte Web", cv="Full stack")
             ⚠ « associer_cv : candidature « Stage développeur full stack… » — Côte Web, « CV Full stack » » ? oui
  [écriture] marquer_envoyee(candidature="Côte Web")        ⚠ confirmé
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

`evaluation/scenarios.json` contient **23 demandes** (15 du jeu `dev`, 8 du jeu `test`, voir Résultats) écrites à la main, chacune avec l'**état attendu** de l'application après le passage de l'agent :
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
python -m agent_first evaluer --threads 4 --pause 10     # écrit evaluation/resultats_llama3.1_8b_v2.md
```

## Résultats

Modèle `llama3.1:8b` servi par Ollama, en local sur un MacBook Air (contexte 4 096 jetons, température 0).

### Version 1 : outils par identifiant (mesurée)

**4 scénarios réussis sur 15 (27 %).** Les 4 réussites sont les demandes où il ne fallait **rien** écrire : les deux refus, la demande ambiguë et le comptage. Les deux garanties de sécurité ont tenu : aucune écriture superflue, aucune écriture après un refus. Détail : [`evaluation/resultats_llama3.1_8b_v1.md`](evaluation/resultats_llama3.1_8b_v1.md).

**Diagnostic, à partir du journal des appels.** Le modèle ne cherche pas les identifiants avant d'agir. Dès le premier tour, il appelle `retenir_offre(offre_id=12345)` ou `associer_cv(candidature_id=12345, cv_id=67890)` avec des identifiants inventés. Face à l'erreur, il demande ensuite l'identifiant à l'utilisateur. Dans ses réponses, il cite aussi des identifiants (« les candidatures 102 et 103 ») au lieu de noms d'entreprises.

**Ce que ça dit de la conception « AI-first ».** Les outils exposaient la logique de la base de données : des identifiants. Or l'utilisateur, et donc l'agent, désigne les choses par leur nom (« Côte Web », « mon CV Data »). Et l'interface ne montre jamais d'identifiant. Le problème vient donc de la conception des outils, pas seulement du modèle.

### Version 2 : outils par référence

Changements faits après la version 1, guidés par les échecs du jeu `dev` :

1. **Références en langage naturel.** Les outils qui agissent sur un objet acceptent « Côte Web », « CV Data » ou un identifiant (`refs.py`). Une seule correspondance : l'action est résolue. Zéro ou plusieurs correspondances : une erreur liste les candidats, et l'agent doit demander à l'utilisateur.
2. **Résolution avant confirmation.** L'humain confirme « retenir_offre : offre « Stage développeur full stack React / Django » — Côte Web (Biarritz) », et non `retenir_offre(5)`. Une référence inventée ou ambiguë n'arrive jamais jusqu'à lui.
3. **Lectures lisibles.** La liste des candidatures donne le titre du CV associé, pas seulement son identifiant. La consigne demande de nommer les entreprises et les postes.

Ces changements ont été conçus en voyant les échecs des scénarios S01 à S15 : sur ce jeu, la mesure est donc optimiste. Pour mesurer sans ce biais, **8 nouveaux scénarios (T01 à T08)** ont été écrits après la version 1 et avant toute exécution de la version 2. Ils reformulent les demandes (« mets de côté », « est partie ce matin », « repousse d'une semaine ») et contiennent une nouvelle demande ambiguë.

### Résultats de la version 2 (mesurés)

| Jeu | Version 1 | Version 2 | Interactions interface → agent (v2) | Écritures après refus |
|---|---|---|---|---|
| `dev` (S01–S15, a guidé les changements) | 4/15 (27 %) | **10/15 (67 %)** | 97 → 25 | 0 |
| `test` (T01–T08, écrit avant la v2) | – | **4/8 (50 %)** | 40 → 14 | 0 |

Durée moyenne : 6 s par demande. Détail : [`evaluation/resultats_llama3.1_8b_v2.md`](evaluation/resultats_llama3.1_8b_v2.md).

**Le chiffre à retenir est celui du jeu `test` : 50 %.** L'écart avec le jeu `dev` (67 %) mesure l'optimisme d'une évaluation faite sur les scénarios qui ont guidé la conception.

**Ce qui fonctionne**
- Les tâches qui portent sur un objet désigné par son nom réussissent presque toujours : marquer une candidature envoyée, décaler une relance, ajouter une note, ignorer une offre.
- Une tâche de 3 écritures enchaînées réussit aussi (S09).
- Les deux demandes ambiguës (S12, T08) donnent lieu à une question, sans aucune écriture.
- Aucune écriture après un refus : c'est garanti par le code.

**Les 9 échecs, regroupés par cause**
1. **Plusieurs objets dans une seule référence** (S06, S13, S15). Le modèle passe « IA, Bordeaux » ou « toutes les candidatures à postuler sans CV » comme une seule référence. Il reçoit l'erreur « ambigu », qui liste les candidats, mais ne reprend pas élément par élément. *Piste : un outil de sélection explicite (lister puis agir sur chaque élément), ou des outils par lot.*
2. **Arguments de lecture remplis au hasard** (S14, T04). Le modèle appelle par exemple `lister_candidatures(entreprise="entreprise")` ou filtre sur le mauvais statut. Le résultat est vide, et la réponse est fausse (« vous n'avez pas envoyé de candidatures »).
3. **Référence bruitée** (S01). Avec « Atlantique Numérique, IA générative, lieu », le mot « lieu » empêche toute correspondance, car le résolveur exige tous les mots. *Piste : une correspondance tolérante, au score.*
4. **Calcul de date** (T05). « Repousser d'une semaine » une relance prévue le 6 donne le 12 au lieu du 13 : le modèle ajoute 7 jours à aujourd'hui. *Piste : un argument `decaler_jours`, calculé par l'application.*
5. **Tâche abandonnée en cours de route** (T06). Après la première écriture, le modèle écrit dans sa réponse l'appel d'un outil qui n'existe pas (`envoyer_cv`) au lieu d'appeler `associer_cv`.
6. **Sens de la demande** (T01). « Mets de côté l'offre » a été compris comme « ignorer », alors que le scénario attendait « retenir ». L'expression est réellement ambiguë en français : la seule écriture non conforme du banc d'essai vient d'une demande mal formulée par l'annotateur autant que d'une erreur du modèle. L'humain a confirmé une action nommée clairement (« ignorer_offre : offre « Stage développeur mobile »… »), et c'est là que la confirmation joue son rôle.

**Conclusion.** Avec un modèle local de 8 milliards de paramètres, ce sont la **conception des outils** (références en langage naturel, résolution par l'application, confirmation d'objets nommés) et les **garde-fous dans le code** qui rendent l'agent utilisable et sûr. La consigne donnée au modèle compte beaucoup moins. Les échecs restants se situent dans les tâches qui portent sur plusieurs éléments, et dans les calculs que l'application devrait faire elle-même.

## Limites

- **Le nombre d'interactions de l'interface** est compté à la main d'après l'interface de StageTrack, et non mesuré sur de vrais utilisateurs.
- **23 scénarios, un seul annotateur, un seul modèle et des données fictives** : c'est un banc d'essai, pas une étude d'usage. Les pourcentages portent sur de petits effectifs (8 scénarios de test). Le taux de réussite dépend fortement du modèle.
- **La confirmation se fait action par action.** Pour une tâche de 10 écritures, une confirmation groupée sur un plan d'actions serait plus pratique. C'est une piste, pas encore implémentée.
- **Agent à un seul tour.** Après une question de l'agent dans un cas ambigu, la conversation ne continue pas.

## Lancer le prototype

Aucune dépendance Python : bibliothèque standard uniquement, et pytest pour les tests.

```bash
brew install ollama && brew services start ollama && ollama pull llama3.1:8b
python -m agent_first parcours                                   # les parcours de l'interface
python -m agent_first demander "Quelles candidatures dois-je relancer cette semaine ?"
python -m agent_first demander "Retiens les deux offres d'IA à Bordeaux."   # demande les confirmations
python -m agent_first evaluer --modele llama3.1:8b
pip install pytest && pytest                                     # 30 tests, sans modèle (modèle scripté)
```

## Organisation

```
agent_first/
  app.py          services de l'application (SQLite), utilisés par l'interface et par l'agent
  journeys.py     parcours de l'interface, étape par étape
  tools.py        services exposés comme outils (schéma JSON, lecture/écriture, parcours remplacé)
  refs.py         résolution des références (« Côte Web », « CV Data ») en objets de l'application
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
