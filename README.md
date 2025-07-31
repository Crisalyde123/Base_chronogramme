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

Pour les opérations de standardisation pilotées par l'IA, renseignez les clefs d'accès
dans les variables d'environnement `OPENAI_API_KEY` ou `MISTRAL_API_KEY` selon
le service utilisé.

## Journaux d'exécution

Chaque lancement du pipeline crée un fichier `run_<horodatage>.log` dans `chronogram_pipeline/data/control/`. Ces journaux sont au format JSON et contiennent les messages techniques ainsi que les métriques de chaque étape du traitement. Ils permettent de tracer précisément les actions réalisées, notamment les appels à l'IA lors de la standardisation des en‑têtes.


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
