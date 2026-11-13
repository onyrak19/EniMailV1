from django.core.management.base import BaseCommand
from accounts.models import User

class Command(BaseCommand):
    help = "Cree (ou met a jour) un compte administrateur"
    def add_arguments(self, p):
        p.add_argument("username"); p.add_argument("email"); p.add_argument("password"); p.add_argument("name", nargs="?", default="Administrateur")
    def handle(self, *a, **o):
        u = User.objects.filter(username=o["username"]).first() or User(username=o["username"])
        u.email, u.first_name, u.role = o["email"].lower(), o["name"], "admin"
        u.is_staff = u.is_superuser = u.is_approved = u.is_active = True
        u.set_password(o["password"]); u.save()
        print("Admin pret :", u.username, "/", u.email)
