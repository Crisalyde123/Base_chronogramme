# Base_chronogramme
Projet de création du pipeline de données pour un base de chronogramme et d'injects.

## Journaux d'exécution

Chaque lancement du pipeline crée un fichier `run_<horodatage>.log` dans
`chronogram_pipeline/data/control/`. Ces journaux sont au format JSON et
contiennent les messages techniques ainsi que les métriques de chaque étape du
traitement. Ils permettent de tracer précisément les actions réalisées,
notamment les appels à l'IA lors de la standardisation des en‑têtes.
