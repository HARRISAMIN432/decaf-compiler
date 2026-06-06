@echo off
echo =========================================
echo Starting Decaf Compiler Project
echo =========================================

echo Starting Python Flask Backend in a new CMD window...
start cmd /k "cd backend && call venv\Scripts\activate && python main.py"

echo Starting React Frontend in a new CMD window...
start cmd /k "cd frontend && npm run dev"

echo =========================================
echo All services are starting up!
echo =========================================
echo.
echo Backend: http://localhost:5000
echo Frontend: http://localhost:5173
echo.
echo Press any key to close this window...
pause > nul