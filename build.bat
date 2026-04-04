@echo off
echo Nettoyage des anciens builds...
rd /s /q build dist 2>nul
del /f /q *.spec 2>nul

echo Compilation de Comte en cours...
:: Remplacement de pyinstaller par python -m PyInstaller
python -m PyInstaller --noconfirm --onefile --windowed ^
    --icon="logo.ico" ^
    --add-data "logo.ico;." ^
    --add-data "grille_shakra_db.json;." ^
    --name "Comte_v1.0.0" ^
    main.py

echo.
echo Termine ! Le fichier se trouve dans le dossier dist.
pause