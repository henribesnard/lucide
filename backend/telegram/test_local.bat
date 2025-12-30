@echo off
REM Script de test local pour le bot Telegram Lucide (Windows)
REM Usage: test_local.bat [polling|webhook|tests]

echo === Lucide Telegram Bot - Test Local ===
echo.

REM Vérifier .env
if not exist .env (
    echo [ERREUR] Fichier .env manquant
    echo Copier .env.example vers .env et configurer votre token:
    echo   copy .env.example .env
    echo   notepad .env
    exit /b 1
)

set MODE=%1
if "%MODE%"=="" set MODE=polling

if "%MODE%"=="polling" (
    echo Mode: Polling ^(Developpement^)
    echo Press Ctrl+C to stop
    echo.
    python -m backend.telegram.run_bot
    goto :eof
)

if "%MODE%"=="webhook" (
    echo Mode: Webhook ^(Production Simulee^)
    echo Assurez-vous qu'un tunnel ^(ngrok/localtunnel^) est actif
    echo.
    python -m backend.telegram.run_bot --webhook --port 8443
    goto :eof
)

if "%MODE%"=="tests" (
    echo Mode: Tests Automatises
    echo Execution de la suite de tests complete...
    echo.
    set DATABASE_URL=sqlite:///:memory:
    pytest -v --cov=. --cov-report=term-missing --cov-report=html
    echo.
    echo Rapport HTML genere dans htmlcov/index.html
    goto :eof
)

if "%MODE%"=="quick-test" (
    echo Mode: Test Rapide
    echo Tests unitaires uniquement...
    echo.
    set DATABASE_URL=sqlite:///:memory:
    pytest tests/unit/ -v
    goto :eof
)

echo Usage: %0 [polling^|webhook^|tests^|quick-test]
echo.
echo Modes:
echo   polling     - Lance le bot en mode polling ^(dev local^)
echo   webhook     - Lance le bot en mode webhook ^(necessite ngrok^)
echo   tests       - Execute tous les tests avec couverture
echo   quick-test  - Execute les tests unitaires uniquement
