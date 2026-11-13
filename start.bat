@echo off
start "ENI Mail - Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && python manage.py runserver"
start "ENI Mail - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 8 >nul
start http://localhost:5173
