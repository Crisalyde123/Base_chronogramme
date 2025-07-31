# Base_chronogramme
Projet de création du pipeline de données pour une base de chronogramme et d'injects.

Ce dépôt contient l'orchestration complète : extraction des fichiers Excel, nettoyage, standardisation et insertion dans une base SQLite. Une présentation détaillée des fichiers est disponible dans [docs/files_overview.md](docs/files_overview.md).

## Journaux d'exécution

Chaque lancement du pipeline crée un fichier `run_<horodatage>.log` dans `chronogram_pipeline/data/control/`. Ces journaux sont au format JSON et contiennent les messages techniques ainsi que les métriques de chaque étape du traitement. Ils permettent de tracer précisément les actions réalisées, notamment les appels à l'IA lors de la standardisation des en‑têtes.


## Déclenchement du pipeline

Les différentes méthodes pour lancer le traitement (formulaire, ligne de commande ou appel automatisé) sont détaillées dans [docs/declenchement.md](docs/declenchement.md).

Pour exécuter le pipeline sur tous les fichiers d'exemple présents dans `data/inputs/`,
lancez simplement :

```bash
python scripts/run_all_inputs.py
```
