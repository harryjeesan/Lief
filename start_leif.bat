@echo off
title Starting Leif
echo =======================================
echo          STARTING LEIF AI
echo =======================================

echo.
echo [1/3] Starting Python Backend Server...
set PYTHONIOENCODING=utf-8
start "Leif Backend (Uvicorn)" cmd /k "set PYTHONIOENCODING=utf-8 && .\venv\Scripts\uvicorn.exe leif.api:app --host 127.0.0.1 --port 8000"

echo [2/3] Starting React Frontend...
cd frontend
start "Leif Frontend (Vite)" cmd /k "npm run dev"

echo [3/3] Opening Leif in your Browser...
timeout /t 3 /nobreak > nul
start http://localhost:5173

echo.
echo =======================================
echo   Leif is now running in the background!
echo   Close the two popup terminal windows to stop her.
echo =======================================
pause
