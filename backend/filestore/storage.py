from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class DatabaseStorage(Storage):
    """Stocke les fichiers dans la base (PostgreSQL) : ils survivent aux redeploiements de Render."""

    def _open(self, name, mode="rb"):
        from .models import StoredFile
        obj = StoredFile.objects.filter(name=name).first()
        if obj is None:
            raise FileNotFoundError(name)
        return ContentFile(bytes(obj.content), name=name)

    def _save(self, name, content):
        from .models import StoredFile
        content.seek(0)
        StoredFile.objects.update_or_create(name=name, defaults={"content": content.read()})
        return name

    def exists(self, name):
        from .models import StoredFile
        return StoredFile.objects.filter(name=name).exists()

    def delete(self, name):
        from .models import StoredFile
        StoredFile.objects.filter(name=name).delete()

    def size(self, name):
        return len(self._open(name).read())

    def url(self, name):
        return settings.MEDIA_URL + name
