import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-key")
# En local : DEBUG actif par defaut. En production (Docker/Render) : DEBUG=0 (defini dans le Dockerfile).
DEBUG = os.getenv("DEBUG", "1") == "1"

RENDER_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME", "")
if DEBUG:
    ALLOWED_HOSTS = ["*"]
else:
    ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]
    if RENDER_HOST:
        ALLOWED_HOSTS.append(RENDER_HOST)
CSRF_TRUSTED_ORIGINS = ["https://" + h for h in ALLOWED_HOSTS if h and h != "*"]
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "rest_framework", "corsheaders", "accounts", "mailbox", "filestore",
]
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware", "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware", "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
ROOT_URLCONF = "eni_mail.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True,
  "OPTIONS": {"context_processors": ["django.template.context_processors.request",
  "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "eni_mail.wsgi.application"
DATABASES = {"default": {"ENGINE": "django.db.backends.postgresql",
  "NAME": os.getenv("DB_NAME", "enimail"), "USER": os.getenv("DB_USER", "postgres"),
  "PASSWORD": os.getenv("DB_PASSWORD", ""), "HOST": os.getenv("DB_HOST", "127.0.0.1"),
  "PORT": os.getenv("DB_PORT", "5432")}}
if os.getenv("DATABASE_URL"):
    DATABASES = {"default": dj_database_url.parse(os.environ["DATABASE_URL"], conn_max_age=600)}
elif os.getenv("DB_ENGINE") == "sqlite":
    # Base SQLite : un simple fichier, aucune installation de PostgreSQL necessaire
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3",
                             "NAME": os.getenv("SQLITE_PATH", str(BASE_DIR / "db.sqlite3"))}}
AUTH_USER_MODEL = "accounts.User"
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Indian/Antananarivo"
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    # FILE_STORAGE=db : fichiers (pieces jointes, avatars) stockes dans la base, donc conserves sur Render
    "default": {"BACKEND": "filestore.storage.DatabaseStorage" if os.getenv("FILE_STORAGE") == "db"
                else "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage" if not DEBUG
                    else "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
# Frontend React compile (copie dans l'image Docker) servi a la racine du site
if (BASE_DIR / "frontend_dist").is_dir():
    WHITENOISE_ROOT = BASE_DIR / "frontend_dist"
    WHITENOISE_INDEX_FILE = True
MEDIA_URL = "/media/"
# Sur Render, pointer MEDIA_ROOT vers un disque persistant (ex: /var/data/media)
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", str(BASE_DIR / "media")))
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CORS_ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"] + [o for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o]
REST_FRAMEWORK = {
  "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
  "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}
from datetime import timedelta
SIMPLE_JWT = {"ACCESS_TOKEN_LIFETIME": timedelta(days=1)}
if os.getenv("EMAIL_MODE") == "smtp":
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "smtp.gmail.com"
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USE_SSL = EMAIL_PORT == 465
    EMAIL_USE_TLS = not EMAIL_USE_SSL
    EMAIL_TIMEOUT = 10
    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
elif os.getenv("EMAIL_MODE") == "brevo":
    # Envoi par API HTTPS (Brevo) : necessaire sur Render gratuit (SMTP bloque)
    EMAIL_BACKEND = "accounts.brevo_backend.BrevoEmailBackend"
    BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "ENI Mail <%s>" % (os.getenv("BREVO_SENDER_EMAIL") or os.getenv("EMAIL_HOST_USER") or "noreply@eni.local")

# 1 = si l'e-mail ne part pas (reseau bloque), l'inscription continue et le code s'affiche dans la console du backend
EMAIL_FALLBACK = os.getenv("EMAIL_FALLBACK", "1") == "1"
