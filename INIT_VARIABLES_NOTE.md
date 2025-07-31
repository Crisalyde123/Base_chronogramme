# Guide d'initialisation des variables

Ce document décrit les éléments à configurer avant d'exécuter le pipeline de chronogramme. Il s'adresse à la personne chargée d'initialiser les variables et les fichiers de référence.

## Emplacement du formulaire

Le formulaire d'envoi d'un nouveau chronogramme enregistre le fichier Excel soumis dans le dossier `data/inputs/` à la racine du projet. Ce répertoire est utilisé par `form_handler.py` pour stocker les fichiers avant traitement. Si vous souhaitez changer cet emplacement, modifiez la constante `INPUTS_DIR` définie dans `chronogram_pipeline/src/form_handler.py`.

## Imposer ou modifier les en-têtes standardisés

- Les correspondances entre en-têtes originaux et en-têtes standard sont stockées dans `config/mapping_headers.csv` (format "En-tete original,En-tete standard").
- Pour ajouter ou modifier un mapping, éditez ce fichier à l'aide d'un tableur puis sauvegardez au format CSV.
- Lors de l'exécution, le pipeline lit ce fichier pour renommer les colonnes. Toute nouvelle correspondance créée par l'IA est également ajoutée dans ce CSV pour validation ultérieure.

## Imposer ou modifier les valeurs standardisées

- Les valeurs à normaliser dans certaines colonnes sont gérées par `config/mapping_values.csv`. Ce fichier comporte trois colonnes : `Colonne`, `Valeur brute` et `Valeur standard`.
- Ajoutez une ligne pour chaque nouvelle valeur à uniformiser. Par exemple :
  ```csv
  Colonne,Valeur brute,Valeur standard
  Type d'inject,Majeur,Critique
  ```
- Une version YAML (`config/value_mappings.yaml`) peut également être utilisée par `standardizer.py` pour stocker ces correspondances.

## Journaux et dossier de contrôle

- Les fichiers de log et le journal `mappings_log.xlsx` sont enregistrés dans `data/control/` par défaut. Vous pouvez rediriger ces fichiers en définissant la variable d'environnement `CHRONO_LOG_DIR` avant d'exécuter le pipeline.

## Schéma cible (optionnel)

Le fichier `config/schema_definition.yaml` définit, lorsque présent, la liste des champs standards attendus ainsi que les valeurs autorisées pour certaines colonnes. Mettez ce fichier à jour si de nouveaux champs doivent être pris en compte.

