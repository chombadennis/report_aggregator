@echo off
echo ===================================================
echo   Starting The Project Local Server
echo ===================================================

echo Starting Python Backend...
start cmd /k "cd backend && call venv\Scripts\activate && python main.py"

echo Starting Next.js Frontend...
start cmd /k "cd frontend && npm run dev"

echo.
echo Application is booting up...
echo Frontend will be accessible at: http://localhost:3000
echo Backend is running at: http://localhost:8000
