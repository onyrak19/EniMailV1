from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

DOMAIN = "enimail.com"


class Level(models.Model):
    """Niveau d'etude (L1, L2, M1...) gere par l'administrateur."""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=60, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "code"]

    def __str__(self): return self.code


class Parcours(models.Model):
    """Parcours / filiere (IG, GB, ASR...) gere par l'administrateur."""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=60, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "code"]
        verbose_name_plural = "parcours"

    def __str__(self): return self.code


class Role(models.Model):
    """Role utilisateur. Les 3 roles systeme (admin, teacher, student) ne peuvent pas etre supprimes."""
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=60)
    is_system = models.BooleanField(default=False)
    has_academic = models.BooleanField(default=False)       # demande niveau + parcours (comme un etudiant)
    requires_approval = models.BooleanField(default=False)  # compte a valider par l'administrateur
    can_broadcast = models.BooleanField(default=False)      # peut envoyer des messages de groupe
    self_register = models.BooleanField(default=False)      # propose a l'inscription

    class Meta:
        ordering = ["id"]

    def __str__(self): return self.code

class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=30, default="student")
    level = models.CharField(max_length=20, blank=True)
    parcours = models.CharField(max_length=20, blank=True)
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
