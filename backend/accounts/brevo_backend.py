import json
import urllib.request
import urllib.error
from email.utils import parseaddr
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class BrevoEmailBackend(BaseEmailBackend):
    """Envoie les e-mails via l'API HTTPS de Brevo (fonctionne sur Render gratuit, contrairement au SMTP)."""
    URL = "https://api.brevo.com/v3/smtp/email"

    def send_messages(self, email_messages):
        sent = 0
        for m in email_messages or []:
            try:
                name, addr = parseaddr(m.from_email or settings.DEFAULT_FROM_EMAIL)
                payload = {
                    "sender": {"name": name or "ENI Mail", "email": addr},
                    "to": [{"email": e} for e in m.to],
                    "subject": m.subject,
                    "textContent": m.body,
                }
                req = urllib.request.Request(
                    self.URL, data=json.dumps(payload).encode("utf-8"), method="POST",
                    headers={"api-key": settings.BREVO_API_KEY, "content-type": "application/json", "accept": "application/json"})
                with urllib.request.urlopen(req, timeout=10) as r:
                    r.read()
                sent += 1
            except urllib.error.HTTPError as e:
                print("Brevo erreur", e.code, e.read().decode("utf-8", "ignore"))
                if not self.fail_silently:
                    raise
            except Exception as e:
                print("Brevo erreur", e)
                if not self.fail_silently:
                    raise
        return sent
