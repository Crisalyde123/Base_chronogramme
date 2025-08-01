# Guide de développement

Ce document explique comment contribuer efficacement au pipeline de traitement des chronogrammes. Il décrit l'architecture générale, les conventions de code et les commandes utiles pour exécuter ou tester le projet.

## Architecture du projet

- **`main.py`** : point d'entrée principal du pipeline.
- **`chronogram_pipeline/`** : dossier contenant le code Python et les tests.
  - `src/` : modules fonctionnels (nettoyage, standardisation, base de données…).
  - `data/` : sous-dossiers `inputs/`, `archive/` et `control/` pour les fichiers d'entrée, l'archivage et les journaux.
  - `output/` : fichiers générés et base SQLite.
  - `config/` : fichiers CSV/YAML de mapping et de schéma.
  - `tests/` : suite de tests `pytest`.
- **`docs/`** : documentations internes.

## Flux d'exécution

`main.py` orchestre les étapes suivantes :
1. **Sélection du fichier** : recherche du dernier fichier Excel dans `data/inputs/` ou utilisation d'un chemin fourni.
2. **Insertion des métadonnées** : enregistrement dans la base via `db_utils.insert_chronogram_metadata()`.
3. **Détection de la feuille** : choix de la feuille principale par `excel_parser.detect_main_sheet()`.
4. **Extraction et nettoyage** : récupération de la table puis nettoyage avec `data_cleaner.clean_data()`.
5. **Standardisation** :
   - en-têtes via `standardizer.standardize_headers()` (fallback IA ou règles).
   - valeurs via `standardizer.standardize_column_values()`.
6. **Enrichissement** : ajout de colonnes contextuelles avec `enricher.enrich_data()`.
7. **Insertion des injects** : écriture dans la table `Injects` et mise à jour du compteur.
8. **Journalisation** : résumé global avec `PipelineLogger.summary()`.

## Ajout d'un nouveau module

1. Créer le fichier dans `chronogram_pipeline/src/` avec une fonction principale de la forme `def run(df: pd.DataFrame, **kwargs) -> pd.DataFrame:`.
2. Ajouter les appels au logger via `get_logger(__name__)`.
3. Documenter les entrées et sorties dans la docstring.
4. Créer un test dans `chronogram_pipeline/tests/` commençant par `test_`.
5. Importer le module dans `src/__init__.py` si besoin pour l'exposer.

## Conventions

- Docstrings au format PEP&nbsp;257.
- Aucune logique dans les `__init__.py` en dehors des exports.
- Fichiers et fonctions en anglais (snake_case).
- Les prompts générés pour l'IA sont stockés dans un dossier `prompts/` créé au besoin.
- Les exceptions sont propagées après avoir été consignées avec `logger.exception()`.

## Journalisation & erreurs

- Utiliser `get_logger()` pour récupérer un logger JSON.
- Les étapes du pipeline sont instrumentées par `PipelineLogger` qui mesure leur durée et produit un récapitulatif.
- Les fichiers de log sont enregistrés dans `data/control/` sauf si la variable `CHRONO_LOG_DIR` redirige vers un autre répertoire.

## Tests

- Tous les tests unitaires se trouvent dans `chronogram_pipeline/tests/`.
- Chaque fonction publique doit être couverte par au moins un test.
- Exécution des tests :
  ```bash
  pytest
  ```

## Bonnes pratiques

- Privilégier des fonctions courtes et atomiques.
- Eviter tout code dans les blocs d'initialisation des modules.
- Les jeux de données de test doivent être réutilisables et placés sous `tests/`.
- Les nouveaux fichiers doivent respecter la structure existante et être référencés dans la documentation.

## Commandes utiles

- Lancer tous les tests : `pytest`
- Traiter un fichier spécifique :
  ```bash
  python main.py --file MON_FICHIER.xlsx
  ```
