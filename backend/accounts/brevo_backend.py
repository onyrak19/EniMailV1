import json
import urllib.request
import urllib.error
from email.utils import parseaddr
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


def explain(code, body):
    """Message lisible selon l'erreur renvoyee par Brevo."""
    b = (body or "").lower()
    if code == 401 and "ip" in b:
        return "Brevo refuse l'adresse IP de cet ordinateur. Dans Brevo : Security > Authorised IPs, desactivez le blocage."
    if code == 401:
        return "Cle API Brevo refusee (incorrecte, incomplete ou supprimee)."
    if code == 400 and "sender" in b:
        return "Expediteur non valide : BREVO_SENDER_EMAIL doit etre une adresse validee dans Brevo (Senders)."
    if code == 403:
        return "Compte Brevo non active ou acces refuse (verifiez le bandeau d'activation dans Brevo)."
    return "Erreur Brevo %s" % code


class BrevoEmailBackend(BaseEmailBackend):
    """Envoie les e-mails via l'API HTTPS de Brevo (fonctionne sur Render gratuit et en local)."""
    URL = "https://api.brevo.com/v3/smtp/email"

    def send_messages(self, email_messages):
        sent = 0
        for m in email_messages or []:
            try:
                if not settings.BREVO_API_KEY:
                    raise RuntimeError("BREVO_API_KEY est vide : verifiez le fichier backend/.env")
                name, addr = parseaddr(m.from_email or settings.DEFAULT_FROM_EMAIL)
                if addr.endswith(".local"):
                    raise RuntimeError("BREVO_SENDER_EMAIL n'est pas defini : verifiez le fichier backend/.env")
                payload = {
                    "sender": {"name": name or "ENI Mail", "email": addr},
                    "to": [{"email": e} for e in m.to],
                    "subject": m.subject,
                    "textContent": m.body,
                }
                req = urllib.request.Request(
                    self.URL, data=json.dumps(payload).encode("utf-8"), method="POST",
                    headers={"api-key": settings.BREVO_API_KEY, "content-type": "application/json", "accept": "application/json"})
                with urllib.request.urlopen(req, timeout=15) as r:
                    r.read()
                sent += 1
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", "ignore")
                msg = explain(e.code, body)
                print("[BREVO] ECHEC :", msg, "| reponse :", body[:300])
                if not self.fail_silently:
                    raise RuntimeError(msg)
            except Exception as e:
                print("[BREVO] ECHEC :", e)
                if not self.fail_silently:
                    raise
        return sent
