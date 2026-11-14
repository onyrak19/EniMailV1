"""Diagnostic e-mail.  Usage (dans backend, venv active) :
      python test_email.py                      -> verifie la configuration
      python test_email.py adresse@gmail.com    -> envoie en plus un vrai e-mail de test
"""
import os, sys, json, socket, smtplib, urllib.request, urllib.error
from dotenv import load_dotenv
here = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(here, ".env")
print("Fichier .env :", env_path, "->", "TROUVE" if os.path.exists(env_path) else "INTROUVABLE (a creer dans le dossier backend)")
load_dotenv(env_path)
mode = (os.getenv("EMAIL_MODE") or "").strip().lower()
key, sender = (os.getenv("BREVO_API_KEY") or "").strip(), (os.getenv("BREVO_SENDER_EMAIL") or "").strip()
if key and mode != "smtp":
    mode = "brevo"
print("Mode e-mail actif :", mode or "console (aucun e-mail reel)")
dest = sys.argv[1] if len(sys.argv) > 1 else None

def call(url, data=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None, method="POST" if data else "GET",
                                 headers={"api-key": key, "content-type": "application/json", "accept": "application/json"})
    return urllib.request.urlopen(req, timeout=15)

if mode == "brevo":
    print("Cle API :", ("presente (%d caracteres, doit commencer par xkeysib-)" % len(key)) if key else "ABSENTE")
    print("Expediteur :", sender or "ABSENT (BREVO_SENDER_EMAIL)")
    try:
        r = socket.create_connection(("api.brevo.com", 443), timeout=8); r.close(); print("Acces a api.brevo.com : OK")
    except Exception as e:
        print("Acces a api.brevo.com : IMPOSSIBLE ->", e, "\n=> Internet bloque ou pare-feu/antivirus. Essayez un autre reseau (partage de connexion du telephone)."); sys.exit(1)
    try:
        info = json.loads(call("https://api.brevo.com/v3/account").read().decode())
        print("Cle API valide. Compte :", info.get("email"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        print("ECHEC cle API (code %s) : %s" % (e.code, body[:300]))
        if e.code == 401 and "ip" in body.lower():
            print("=> Brevo bloque cette adresse IP : Security > Authorised IPs > desactivez le blocage.")
        elif e.code == 401:
            print("=> Cle incorrecte ou incomplete : regenerez-en une dans Brevo (SMTP & API > API Keys) et recopiez-la en entier dans .env.")
        sys.exit(1)
    except Exception as e:
        print("ECHEC :", e); sys.exit(1)
    if dest:
        try:
            call("https://api.brevo.com/v3/smtp/email", {"sender": {"name": "ENI Mail", "email": sender}, "to": [{"email": dest}],
                                                         "subject": "Test ENI Mail", "textContent": "Si vous lisez ceci, l'envoi d'e-mails fonctionne."}).read()
            print("OK : e-mail de test envoye a", dest, "(verifiez aussi les spams).")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")
            print("ECHEC envoi (code %s) : %s" % (e.code, body[:300]))
            if "sender" in body.lower():
                print("=> L'expediteur", sender, "n'est pas valide dans Brevo : Senders, Domains & Dedicated IPs > Senders (statut Verified).")
        except Exception as e:
            print("ECHEC envoi :", e)
    else:
        print("Pour tester un vrai envoi : python test_email.py votre.adresse@gmail.com")
elif mode == "smtp":
    host = "smtp.gmail.com"
    for port in (587, 465):
        try:
            socket.create_connection((host, port), timeout=8).close(); print("Port", port, ": ACCESSIBLE")
        except Exception as e:
            print("Port", port, ": BLOQUE ->", e)
    user, pwd, port = os.getenv("EMAIL_HOST_USER"), os.getenv("EMAIL_HOST_PASSWORD"), int(os.getenv("EMAIL_PORT", "587"))
    try:
        s = smtplib.SMTP_SSL(host, 465, timeout=10) if port == 465 else smtplib.SMTP(host, 587, timeout=10)
        if port != 465: s.starttls()
        s.login(user, pwd); s.quit(); print("OK : connexion Gmail reussie.")
    except smtplib.SMTPAuthenticationError:
        print("Reseau OK mais identifiants refuses : mot de passe d'application incorrect ou revoque.")
    except Exception as e:
        print("ECHEC :", e, "\n=> Si les ports sont BLOQUES, utilisez Brevo (EMAIL_MODE=brevo + BREVO_API_KEY).")
else:
    print("Aucun e-mail reel ne partira : ajoutez BREVO_API_KEY et BREVO_SENDER_EMAIL dans backend/.env")
