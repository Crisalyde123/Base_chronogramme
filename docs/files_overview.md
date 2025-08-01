# Aperçu des fichiers

Ce document résume brièvement le rôle des principaux fichiers du projet.

## Racine du dépôt

- **`main.py`** : point d'entrée du pipeline. Orchestration de l'import des fichiers Excel, du nettoyage et de l'insertion en base.
- **`README.md`** : vue d'ensemble rapide du projet et des journaux d'exécution.
- **`Specifications_techniques.md`** : spécifications détaillées du pipeline et des choix techniques.
- **`retest_env.ps1`** : script PowerShell pour tester l'environnement (installation des dépendances et exécution des tests).
- **`requirements.txt`** : dépendances Python nécessaires au fonctionnement du projet.
- **`scripts/process_new_inputs.py`** : traite tous les fichiers présents dans
  `data/inputs/` puis les archive automatiquement.

## Répertoire `config/`

- **`mapping_headers.csv`** : correspondances entre intitulés d'en‑têtes et champs standards.
- **`mapping_values.csv`** : correspondances de valeurs pour certaines colonnes.
- **`value_mappings.yaml`** : version YAML des règles de mapping de valeurs.

## Répertoire `chronogram_pipeline/`

Contient le code principal du pipeline ainsi que les tests.

- **`README.md`** : présentation rapide du dossier.
- **`data/`** : dossiers `inputs`, `archive` et `control` utilisés respectivement pour les fichiers à traiter, l'archivage et les journaux JSON.
- **`output/`** : emplacement par défaut pour les fichiers générés et la base SQLite.
- **`src/`** : implémentation des différentes briques de traitement (voir plus bas).
- **`tests/`** : suite de tests automatisés utilisables avec `pytest`.

### Modules du dossier `src/`

- **`excel_parser.py`** : détection de la feuille principale dans un classeur Excel et extraction de la table de données.
- **`data_cleaner.py`** : utilitaires de nettoyage (suppression de lignes/colonnes vides, propagation de cellules fusionnées).
- **`standardizer.py`** : fonctions de standardisation des en‑têtes et des valeurs à l'aide de dictionnaires ou d'appels IA.
- **`mapping_utils.py`** : aide au chargement et à la mise à jour des fichiers de mapping.
- **`db_utils.py`** : création et manipulation de la base SQLite du projet.
- **`enricher.py`** : ajouts de colonnes ou calculs complémentaires avant insertion.
- **`pipeline_logger.py`** et **`logger.py`** : configuration du logger JSON et gestion des messages durant l'exécution.
- **`form_handler.py`** : traitement des formulaires côté front pour enregistrer un nouveau chronogramme.
- **`manual_table_extractor.py`** : extraction manuelle d'une table lorsqu'aucune heuristique automatique ne fonctionne.
- **`init_db.py`** : création initiale des bases de données et des tables \
  (à lancer avec `python -m chronogram_pipeline.src.init_db`).

