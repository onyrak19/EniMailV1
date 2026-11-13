import os, socket, smtplib
from dotenv import load_dotenv
load_dotenv()
host = "smtp.gmail.com"
print("=== Test de connexion a Gmail ===")
for port in (587, 465):
    try:
        socket.create_connection((host, port), timeout=8).close(); print("Port", port, ": ACCESSIBLE")
    except Exception as e:
        print("Port", port, ": BLOQUE ->", e)
user, pwd, port = os.getenv("EMAIL_HOST_USER"), os.getenv("EMAIL_HOST_PASSWORD"), int(os.getenv("EMAIL_PORT", "587"))
print("Test d'identifiants sur le port", port, "...")
try:
    if port == 465:
        s = smtplib.SMTP_SSL(host, 465, timeout=10)
    else:
        s = smtplib.SMTP(host, 587, timeout=10); s.starttls()
    s.login(user, pwd); s.quit(); print("OK : connexion Gmail reussie, les e-mails peuvent partir.")
except smtplib.SMTPAuthenticationError:
    print("Reseau OK mais identifiants refuses : mot de passe d'application incorrect ou revoque.")
except Exception as e:
    print("ECHEC :", e)
