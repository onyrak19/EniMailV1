from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

LEVELS = ["L1", "L2", "L3", "M1", "M2"]
PARCOURS = ["IG", "GB", "ASR", "MDI"]
DOMAIN = "enimail.com"

class User(AbstractUser):
    ROLES = [("admin", "Administrateur"), ("teacher", "Professeur"), ("student", "Etudiant")]
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLES, default="student")
    level = models.CharField(max_length=3, blank=True)
    parcours = models.CharField(max_length=5, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    avatar = models.FileField(upload_to="avatars/", blank=True)
    is_approved = models.BooleanField(default=True)
    notify_by_email = models.BooleanField(default=True)

    @property
    def address(self):
        return "%s@%s" % (self.username.lower(), DOMAIN)

    @property
    def display(self):
        return self.get_full_name() or self.username

class EmailCode(models.Model):
    email = models.EmailField()
    purpose = models.CharField(max_length=10, default="register")
    code = models.CharField(max_length=6)
    attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
