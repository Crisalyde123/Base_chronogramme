# retest_env.ps1
# Script pour re-tester l’environnement global Python complet

Write-Host "=== 📦 Installation des dépendances ==="
pip install -r requirements.txt

Write-Host "`n=== 🛠 Initialisation des bases SQLite ==="
python -m chronogram_pipeline.src.init_db

Write-Host "`n=== 📂 Vérification des fichiers .db ==="
Get-ChildItem .\chronogram_pipeline\output\databases

Write-Host "`n=== 🧪 Lancement de tous les tests Pytest ==="
pytest

Write-Host "`n=== ✅ Fin du test environnement ==="
