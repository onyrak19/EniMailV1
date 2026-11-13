import mimetypes
from django.contrib import admin
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404
from django.urls import path, include, re_path


def media(request, path):
    """Sert les fichiers /media/ (avatars...) depuis le stockage actif (disque ou base de donnees)."""
    try:
        f = default_storage.open(path)
    except Exception:
        raise Http404
    return FileResponse(f, content_type=mimetypes.guess_type(path)[0] or "application/octet-stream")


urlpatterns = [
    path("admin/", admin.site.urls), path("api/", include("accounts.urls")), path("api/", include("mailbox.urls")),
    re_path(r"^media/(?P<path>.*)$", media),
]
