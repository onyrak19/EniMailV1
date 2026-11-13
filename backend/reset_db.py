import os, shutil
from dotenv import load_dotenv
load_dotenv()
here = os.path.dirname(os.path.abspath(__file__))
if os.getenv("DB_ENGINE") == "sqlite":
    path = os.getenv("SQLITE_PATH", os.path.join(here, "db.sqlite3"))
    if os.path.exists(path): os.remove(path)
else:
    import psycopg2
    name = os.getenv("DB_NAME", "enimail")
    c = psycopg2.connect(dbname="postgres", user=os.getenv("DB_USER", "postgres"), password=os.getenv("DB_PASSWORD", ""),
                         host=os.getenv("DB_HOST", "127.0.0.1"), port=os.getenv("DB_PORT", "5432"))
    c.autocommit = True
    cur = c.cursor()
    cur.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s AND pid<>pg_backend_pid()", (name,))
    cur.execute('DROP DATABASE IF EXISTS "%s"' % name)
    cur.execute('CREATE DATABASE "%s"' % name)
shutil.rmtree(os.path.join(here, "media"), ignore_errors=True)
print("Base reinitialisee (vide) et fichiers supprimes")
