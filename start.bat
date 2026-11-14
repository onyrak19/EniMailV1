@echo off
start "ENI Mail - Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && pip install -q -r requirements.txt && python manage.py migrate && python manage.py runserver"
start "ENI Mail - Frontend" cmd /k "cd /d %~dp0frontend && npm install && npm run dev"
timeout /t 15 >nul
start http://localhost:5173
