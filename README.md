# ENI Mail
## Test en local (sans PostgreSQL, sans Docker)
Pre-requis : Python (PATH) et Node.js LTS.
1. Dans backend, creer le fichier .env (copie de .env.example) avec DB_ENGINE=sqlite
2. setup.bat (une seule fois)
3. Dans backend (venv active) : python manage.py createadmin admin onirak19@gmail.com admin123 "Administrateur"
4. start.bat -> http://localhost:5173
Les codes de verification s'affichent dans la fenetre noire du backend.
Reinitialiser : python reset_db.py (dans backend, venv active)
