from django.db import models


class StoredFile(models.Model):
    """Contenu d'un fichier (piece jointe, avatar) stocke dans la base de donnees."""
    name = models.CharField(max_length=255, unique=True)
    content = models.BinaryField()
