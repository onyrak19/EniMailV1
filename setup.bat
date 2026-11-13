@echo off
echo === ENI Mail : installation ===
cd /d %~dp0backend
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
echo.
set /p ans=Effacer la base de donnees existante et repartir de zero ? (O/N) : 
if /i "%ans%"=="O" (python reset_db.py) else (python create_db.py)
python manage.py migrate
cd /d %~dp0frontend
call npm install
echo.
echo === Installation terminee ===
echo Creez maintenant le compte admin (voir README), puis lancez start.bat
pause
