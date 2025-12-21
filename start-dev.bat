@echo off
echo ========================================
echo Lucide - Demarrage en mode developpement
echo ========================================
echo.

echo [1/2] Demarrage du backend (Docker)...
start /B docker-compose -f docker-compose-backend-only.yml up

echo.
echo [2/2] Attente du backend (10 secondes)...
timeout /t 10 /nobreak > nul

echo.
echo [3/3] Demarrage du frontend (local)...
cd frontend
start cmd /k "npm run dev"

echo.
echo ========================================
echo Services demarres:
echo - Backend: http://localhost:8001
echo - Frontend: http://localhost:3010
echo ========================================
echo.
echo Appuyez sur une touche pour quitter...
pause > nul
