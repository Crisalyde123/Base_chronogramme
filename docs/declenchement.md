# Déclenchement du pipeline

Ce document décrit les différentes manières d'initialiser le pipeline de traitement des chronogrammes. Chaque méthode doit fournir au moins un fichier Excel (`.xlsx`) et les métadonnées associées :

- `nom_chronogramme`
- `etablissement_nom`
- `etablissement_type`
- `date_exercice`
- `submitter`

Le fichier est stocké dans `data/inputs/` puis traité par `main.py`.

## 1. Depuis un formulaire utilisateur

1. L'utilisateur renseigne les champs du formulaire : nom du chronogramme, établissement (nom et type), date de l'exercice, nom du soumissionnaire et charge le fichier Excel.
2. `form_handler.py` enregistre le fichier dans `data/inputs/` via `save_excel_file()`.
3. Les métadonnées sont insérées dans la table `Chronogrammes` à l'aide de `insert_chronogram()`.
4. Le script `main.py` est lancé avec le fichier ainsi sauvegardé pour réaliser l'ensemble du pipeline.

## 2. En ligne de commande

1. Copier un fichier dans `data/inputs/` ou fournir un chemin absolu.
2. Exécuter :
   ```bash
   python main.py --file "data/inputs/Chronogramme_XXX_YYY.xlsx"
   ```
   Optionnellement, les métadonnées peuvent être passées en JSON :
   ```bash
   python main.py --file "data/inputs/Chronogramme_XXX_YYY.xlsx" \
       --meta '{"nom_chronogramme": "Exercice X", "etablissement_nom": "Hôpital", "etablissement_type": "CH", "date_exercice": "2024-01-01", "submitter": "admin"}'
   ```
   Si elles ne sont pas fournies, `main.py` tente de les déduire à partir du nom du fichier.

## 3. Via un script automatisé (cron, API…)

Une tâche planifiée peut appeler le script `scripts/process_new_inputs.py` qui
recherche tous les fichiers `.xlsx` dans `data/inputs/`. Pour chacun, il lance
`main.py` puis déplace le fichier traité dans `data/archive/raw_excels/` avec un
horodatage. Ce script constitue le point d'entrée recommandé pour automatiser le
traitement continu.

## 4. Traitement en lot des échantillons

Pour exécuter la chaîne complète sur tous les fichiers `.xlsx` présents dans `data/inputs/`,
utilisez le script `scripts/run_all_inputs.py` :

```bash
python scripts/run_all_inputs.py
```
On peut aussi lui passer un dossier en argument :
```bash
python scripts/run_all_inputs.py /autre/dossier
```

## Erreurs courantes

- **Fichier manquant ou extension incorrecte** : `FileNotFoundError` ou `ValueError` si l'argument `--file` ne désigne pas un `.xlsx` existant.
- **Métadonnées incomplètes** : `insert_chronogram_metadata()` lève une `ValueError` lorsque des champs requis sont absents.
- **Problème de chemin** : vérifier que `CHRONO_LOG_DIR` et `PYTHONPATH` sont correctement définis si les logs ou les modules ne sont pas trouvés.

## Tests rapides

1. Soumettre un fichier via le formulaire et vérifier que l'identifiant du chronogramme est créé.
2. Lancer `main.py` avec un fichier valide et observer la création des logs dans `data/control/`.
3. Tester l'appel avec des métadonnées manquantes pour confirmer que le pipeline signale l'erreur.
