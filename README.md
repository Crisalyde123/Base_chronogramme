# Base_chronogramme
Projet de création du pipeline de données pour une base de chronogramme et d'injects.

Ce dépôt contient l'orchestration complète : extraction des fichiers Excel, nettoyage, standardisation et insertion dans une base SQLite. Une présentation détaillée des fichiers est disponible dans [docs/files_overview.md](docs/files_overview.md).

## Installation

1. Créez un environnement virtuel Python (>=3.10) :
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
3. Initialisez les bases SQLite :
   ```bash
   python chronogram_pipeline/src/init_db.py
   ```
   Vous pouvez également lancer le script depuis son dossier :
   ```bash
   cd chronogram_pipeline/src
   python init_db.py
   ```
   ou via le module Python :
   ```bash
   python -m chronogram_pipeline.src.init_db
   ```

Pour les opérations de standardisation pilotées par l'IA, renseignez les clefs d'accès
dans les variables d'environnement `OPENAI_API_KEY` ou `MISTRAL_API_KEY` selon
le service utilisé.

## Mapping manuel

- Le dossier `mapping/` contient les références utilisées par le pipeline :

- `colonnes.csv` : colonnes `chronogramme`, `raw_name` et `mapped_name`.
  Les nouvelles colonnes rencontrées sont ajoutées avec `mapped_name` mis à `X`.
- `valeurs.csv` : colonnes `chronogramme`, `column_name`, `raw_value` et
  `mapped_value`. Les valeurs inconnues sont ajoutées avec `mapped_value` à `X`.
- `colonnes_standardisees.csv` : liste des noms de colonnes cibles possibles.
- `valeurs_standardisees.csv` : valeurs autorisées pour certaines colonnes.

Après avoir complété `colonnes.csv` ou `valeurs.csv`, relancez le pipeline pour
reprendre le traitement.

## Journaux d'exécution

Chaque lancement du pipeline crée un fichier `run_<horodatage>.log` dans `chronogram_pipeline/data/control/`. Ces journaux sont au format JSON et contiennent les messages techniques ainsi que les métriques de chaque étape du traitement. Ils permettent de tracer précisément les actions réalisées, notamment les appels à l'IA lors de la standardisation des en‑têtes.

Un script de suivi `scripts/monitor_kpi.py` agrège ces journaux et le fichier `mappings_log.xlsx` afin de générer un rapport `monitoring_log.md` avec les principaux indicateurs (taux d'automatisation, recours à l'IA, complétude des données...).


## Déclenchement du pipeline

Les différentes méthodes pour lancer le traitement (formulaire, ligne de commande ou appel automatisé) sont détaillées dans [docs/declenchement.md](docs/declenchement.md).

Pour exécuter le pipeline sur tous les fichiers d'exemple présents dans `data/inputs/`,
pour traiter tous les exemples, lancez simplement :

```bash
python scripts/run_all_inputs.py
```
Vous pouvez aussi indiquer un autre dossier contenant des fichiers Excel :
```bash
python scripts/run_all_inputs.py /chemin/vers/mes_fichiers
```
Pour une automatisation complète, le script `scripts/process_new_inputs.py`
traite tous les fichiers présents dans `data/inputs/` puis les déplace
automatiquement dans `data/archive/raw_excels/`.
