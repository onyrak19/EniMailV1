import re, secrets, threading
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User, EmailCode, LEVELS, PARCOURS, DOMAIN

IMG = (".png", ".jpg", ".jpeg", ".gif", ".webp")
ROLES = ("admin", "teacher", "student")
PUBLIC = [api_view, ]

def ser(u):
    return {"id": u.id, "name": u.display, "username": u.username, "email": u.email, "role": u.role, "level": u.level,
            "parcours": u.parcours, "phone": u.phone, "avatar": u.avatar.url if u.avatar else "", "notify": u.notify_by_email,
            "approved": u.is_approved, "active": u.is_active, "address": u.address, "joined": u.date_joined.strftime("%d/%m/%Y")}

def pub(u):
    return {"id": u.id, "name": u.display, "username": u.username, "address": u.address, "role": u.role,
            "level": u.level, "parcours": u.parcours, "avatar": u.avatar.url if u.avatar else ""}

def mail_failed(e):
    print("Echec envoi e-mail:", e)
    if settings.EMAIL_FALLBACK:
        return Response({"ok": True, "warning": "L'e-mail n'a pas pu etre envoye (reseau bloque). Le code est affiche dans la fenetre noire du backend."})
    return bad("Envoi du code impossible (verifiez la configuration e-mail)", 502)

def bad(msg, code=400): return Response({"error": msg}, status=code)

def mail_async(subject, text, to):
    to = [e for e in to if e and not e.endswith(".local")]
    if not to: return
    def run():
        try: send_mail(subject, text, None, to)
        except Exception as e: print("Mail non envoye:", e)
    threading.Thread(target=run, daemon=True).start()

def check_username(v, exclude=None):
    if not re.fullmatch(r"[A-Za-z0-9._-]{3,30}", v or ""):
        return "Nom d'utilisateur invalide (3 a 30 caracteres : lettres, chiffres, . _ -)"
    qs = User.objects.filter(username__iexact=v)
    if exclude: qs = qs.exclude(pk=exclude.pk)
    if qs.exists(): return "Ce nom d'utilisateur est deja pris"

def academic(role, d):
    if role != "student": return "", ""
    return (d.get("level") if d.get("level") in LEVELS else ""), (d.get("parcours") if d.get("parcours") in PARCOURS else "")

def send_code(email, purpose, subject):
    code = "%06d" % secrets.randbelow(1000000)
    EmailCode.objects.filter(email=email, purpose=purpose).delete()
    EmailCode.objects.create(email=email, purpose=purpose, code=code)
    print("[CODE]", purpose, email, code)
    send_mail(subject, "Votre code ENI Mail : %s\nIl expire dans 10 minutes." % code, None, [email], fail_silently=False)

def check_code(email, purpose, code):
    rec = EmailCode.objects.filter(email=email, purpose=purpose).first()
    if not rec or timezone.now() - rec.created_at > timedelta(minutes=10) or rec.attempts >= 5: return None
    if rec.code != (code or "").strip():
        rec.attempts += 1; rec.save(); return None
    return rec

def find(v):
    v = (v or "").strip()
    return User.objects.filter(Q(username__iexact=v) | Q(email__iexact=v)).first() if v else None

class LoginSer(TokenObtainPairSerializer):
    def validate(self, attrs):
        found = find(attrs["username"])
        attrs["username"] = found.username if found else attrs["username"].strip()
        data = super().validate(attrs)
        if not self.user.is_approved:
            raise PermissionDenied("Compte professeur en attente de validation par l'administrateur.")
        data["user"] = ser(self.user)
        return data

class LoginView(TokenObtainPairView):
    serializer_class = LoginSer

def public(fn):
    return api_view(["POST"])(authentication_classes([])(permission_classes([AllowAny])(fn)))

@public
def request_code(request):
    email = (request.data.get("email") or "").strip().lower()
    if "@" not in email: return bad("Adresse e-mail invalide")
    if User.objects.filter(email__iexact=email).exists(): return bad("Cette adresse est deja inscrite")
    try: send_code(email, "register", "Votre code ENI Mail")
    except Exception as e:
        return mail_failed(e)
    return Response({"ok": True})

@public
def register(request):
    d = request.data
    email = (d.get("email") or "").strip().lower()
    name, role, username = (d.get("name") or "").strip(), d.get("role"), (d.get("username") or "").strip()
    e = check_username(username)
    if e: return bad(e)
    if not name or role not in ("student", "teacher") or len(d.get("password") or "") < 6:
        return bad("Nom, role et mot de passe (6 caracteres min.) requis")
    level, parcours = academic(role, d)
    if role == "student" and not (level and parcours): return bad("Niveau et parcours requis")
    if User.objects.filter(email__iexact=email).exists(): return bad("Cette adresse est deja inscrite")
    rec = check_code(email, "register", d.get("code"))
    if not rec: return bad("Code incorrect ou expire")
    u = User.objects.create_user(username=username, email=email, password=d["password"], first_name=name, role=role,
                                 level=level, parcours=parcours, is_approved=(role == "student"))
    rec.delete()
    mail_async("Bienvenue sur ENI Mail", "Bonjour %s,\n\nVotre compte ENI Mail est cree.\nVotre adresse ENI Mail : %s\nNom d'utilisateur : %s\n%s" % (name, u.address, u.username, "Un administrateur doit valider votre compte professeur." if role == "teacher" else "Vous pouvez vous connecter."), [email])
    if role == "teacher":
        for a in User.objects.filter(role="admin", is_active=True, notify_by_email=True):
            mail_async("Nouvelle inscription professeur - ENI Mail",
                       "Bonjour %s,\n\n%s (%s) demande la validation de son compte professeur.\nConnectez-vous a ENI Mail > Administration pour la valider ou la refuser." % (a.display, name, email), [a.email])
    return Response({"pending": not u.is_approved, "address": u.address}, status=201)

@public
def password_code(request):
    u = find(request.data.get("identifier"))
    if u and u.is_active:
        try: send_code(u.email, "reset", "Reinitialisation de votre mot de passe ENI Mail")
        except Exception as e:
            return mail_failed(e)
    return Response({"ok": True})

@public
def password_reset(request):
    d = request.data
    u = find(d.get("identifier"))
    if len(d.get("password") or "") < 6: return bad("Mot de passe trop court (6 caracteres min.)")
    rec = check_code(u.email, "reset", d.get("code")) if u else None
    if not rec: return bad("Code incorrect ou expire")
    u.set_password(d["password"]); u.save(); rec.delete()
    return Response({"ok": True})

@api_view(["GET", "PATCH"])
def me(request):
    u, d = request.user, request.data
    if request.method == "PATCH":
        if "username" in d and d["username"].strip() != u.username:
            e = check_username(d["username"].strip(), u)
            if e: return bad(e)
            u.username = d["username"].strip()
        if d.get("name"): u.first_name, u.last_name = d["name"].strip(), ""
        if "phone" in d: u.phone = (d["phone"] or "")[:30]
        if "notify" in d: u.notify_by_email = bool(d["notify"])
        if u.role == "student":
            if d.get("level") in LEVELS: u.level = d["level"]
            if d.get("parcours") in PARCOURS: u.parcours = d["parcours"]
        u.save()
    return Response(ser(u))

@api_view(["POST"])
def me_password(request):
    u, d = request.user, request.data
    if not u.check_password(d.get("old") or ""): return bad("Ancien mot de passe incorrect")
    if len(d.get("new") or "") < 6: return bad("Nouveau mot de passe trop court (6 caracteres min.)")
    u.set_password(d["new"]); u.save()
    return Response({"ok": True})

@api_view(["POST", "DELETE"])
def me_avatar(request):
    u = request.user
    if request.method == "DELETE":
        u.avatar = ""; u.save()
    else:
        f = request.FILES.get("file")
        if not f or not f.name.lower().endswith(IMG): return bad("Image requise (png, jpg, gif, webp)")
        if f.size > 3 * 1024 * 1024: return bad("Image trop lourde (3 Mo max)")
        u.avatar = f; u.save()
    return Response(ser(u))

@api_view(["GET"])
def users(request):
    g = request.GET
    raw = g.get("q", "").strip()
    q = raw.lower().replace("@" + DOMAIN, "")
    if q == "enimail": q = ""
    qs = User.objects.filter(is_approved=True, is_active=True).exclude(id=request.user.id)
    if q: qs = qs.filter(Q(first_name__icontains=q) | Q(username__icontains=q) | Q(email__iexact=raw))
    if g.get("role") in ROLES: qs = qs.filter(role=g["role"])
    if g.get("level") in LEVELS: qs = qs.filter(level=g["level"])
    if g.get("parcours") in PARCOURS: qs = qs.filter(parcours=g["parcours"])
    return Response([pub(u) for u in qs.order_by("first_name")[:60 if g.get("full") else 20]])

@api_view(["GET"])
def resolve(request):
    v = (request.GET.get("v") or "").strip().lower()
    if v.endswith("@" + DOMAIN): v = v[:-len(DOMAIN) - 1]
    u = User.objects.filter(Q(username__iexact=v) | Q(email__iexact=(request.GET.get("v") or "").strip()), is_approved=True, is_active=True).exclude(pk=request.user.pk).first()
    return Response(pub(u)) if u else bad("Utilisateur introuvable", 404)

def _admin(request):
    if request.user.role != "admin": raise PermissionDenied("Reserve a l'administrateur")

@api_view(["GET"])
def pending(request):
    _admin(request)
    return Response([ser(u) for u in User.objects.filter(role="teacher", is_approved=False)])

@api_view(["POST"])
def approve(request, pk):
    _admin(request)
    u = get_object_or_404(User, pk=pk, role="teacher")
    u.is_approved = True; u.save()
    mail_async("Compte ENI Mail valide", "Bonjour %s, votre compte professeur a ete valide.\nVotre adresse ENI Mail : %s\nVous pouvez vous connecter." % (u.display, u.address), [u.email])
    return Response({"ok": True})

@api_view(["POST"])
def reject(request, pk):
    _admin(request)
    u = User.objects.filter(pk=pk, role="teacher", is_approved=False).first()
    if u:
        mail_async("Inscription ENI Mail refusee", "Bonjour %s, votre demande de compte professeur a ete refusee." % u.display, [u.email]); u.delete()
    return Response({"ok": True})

@api_view(["GET", "POST"])
def admin_users(request):
    _admin(request)
    if request.method == "POST":
        d = request.data
        username, email, role = (d.get("username") or "").strip(), (d.get("email") or "").strip().lower(), d.get("role")
        e = check_username(username)
        if e: return bad(e)
        if "@" not in email or User.objects.filter(email__iexact=email).exists(): return bad("E-mail invalide ou deja utilise")
        if role not in ROLES or not (d.get("name") or "").strip() or len(d.get("password") or "") < 6:
            return bad("Nom, role et mot de passe (6 caracteres min.) requis")
        level, parcours = academic(role, d)
        u = User.objects.create_user(username=username, email=email, password=d["password"], first_name=d["name"].strip(), role=role,
                                     level=level, parcours=parcours, is_staff=role == "admin", is_superuser=role == "admin")
        return Response(ser(u), status=201)
    q, role = request.GET.get("q", "").strip(), request.GET.get("role", "")
    qs = User.objects.all().order_by("role", "first_name")
    if q: qs = qs.filter(Q(first_name__icontains=q) | Q(email__icontains=q) | Q(username__icontains=q))
    if role in ROLES: qs = qs.filter(role=role)
    return Response([ser(u) for u in qs[:300]])

@api_view(["PATCH", "DELETE"])
def admin_user(request, pk):
    _admin(request)
    u, d = get_object_or_404(User, pk=pk), request.data
    if request.method == "DELETE":
        if u == request.user: return bad("Vous ne pouvez pas supprimer votre propre compte")
        u.delete(); return Response({"ok": True})
    if u == request.user and (d.get("role", "admin") != "admin" or d.get("is_active", True) is False):
        return bad("Vous ne pouvez pas retirer vos propres droits")
    if "username" in d and d["username"].strip() != u.username:
        e = check_username(d["username"].strip(), u)
        if e: return bad(e)
        u.username = d["username"].strip()
    if "email" in d:
        em = d["email"].strip().lower()
        if "@" not in em or User.objects.filter(email__iexact=em).exclude(pk=u.pk).exists(): return bad("E-mail invalide ou deja utilise")
        u.email = em
    if d.get("name"): u.first_name, u.last_name = d["name"].strip(), ""
    if d.get("role") in ROLES:
        u.role = d["role"]; u.is_staff = u.is_superuser = (u.role == "admin")
    if "is_active" in d: u.is_active = bool(d["is_active"])
    if "is_approved" in d: u.is_approved = bool(d["is_approved"])
    if d.get("password"):
        if len(d["password"]) < 6: return bad("Mot de passe trop court (6 caracteres min.)")
        u.set_password(d["password"])
    u.level, u.parcours = academic(u.role, {"level": d.get("level", u.level), "parcours": d.get("parcours", u.parcours)})
    u.save()
    return Response(ser(u))
