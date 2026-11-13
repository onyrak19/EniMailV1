import os, psycopg2
from dotenv import load_dotenv
load_dotenv()
if os.getenv("DB_ENGINE") == "sqlite":
    print("Mode SQLite : rien a creer (le fichier db.sqlite3 sera cree automatiquement)")
    raise SystemExit(0)
c = psycopg2.connect(dbname="postgres", user=os.getenv("DB_USER", "postgres"), password=os.getenv("DB_PASSWORD", ""),
                     host=os.getenv("DB_HOST", "127.0.0.1"), port=os.getenv("DB_PORT", "5432"))
c.autocommit = True
cur = c.cursor()
name = os.getenv("DB_NAME", "enimail")
cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (name,))
if cur.fetchone():
    print("Base", name, "deja existante")
else:
    cur.execute('CREATE DATABASE "%s"' % name)
    print("Base", name, "creee")
