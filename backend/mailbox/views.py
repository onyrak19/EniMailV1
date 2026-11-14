import json, os, threading
from django.core.mail import get_connection, EmailMessage
from django.db.models import Q
from django.http import FileResponse
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from accounts.models import User, Role
from .models import Message, Recipient, Attachment

APP_URL = os.getenv("APP_URL", "http://localhost:5173")
BLOCKED = (".exe", ".bat", ".cmd", ".com", ".scr", ".msi", ".vbs", ".jar", ".ps1")
MAX_FILE, MAX_FILES = 10 * 1024 * 1024, 10

def _send_alerts(items):
    try:
        conn = get_connection()
        msgs = []
        for e, n, s, sub, body, natt in items:
            text = "Bonjour %s,\n\nVous avez un nouveau message de %s sur votre adresse ENI Mail.\nObjet : %s\n" % (n, s, sub)
            if body is not None:
                text += "\n----------------------------------------\n%s\n----------------------------------------\n" % body
                if natt: text += "\nPieces jointes : %d (a telecharger dans ENI Mail).\n" % natt
            text += "\nOuvrez ENI Mail : %s" % APP_URL
            msgs.append(EmailMessage(("ENI Mail : " + sub) if body is not None else "Nouveau message sur ENI Mail", text, None, [e], connection=conn))
        conn.send_messages(msgs)
    except Exception as ex:
        print("Alertes e-mail non envoyees:", ex)

def notify(users, sender, subject, body=None, natt=0):
    """body=None : simple alerte (objet seulement). body=texte : le contenu du message est aussi envoye par e-mail."""
    items = [(u.email, u.display, sender.display, subject or "(sans objet)", body, natt) for u in users if u.notify_by_email and not u.email.endswith(".local")]
    if items: threading.Thread(target=_send_alerts, args=(items,), daemon=True).start()

def _atts(m): return [{"id": a.id, "name": a.name, "size": a.size} for a in m.attachments.all()]

def card(m, rid=None, r=None, to=""):
    s = m.sender
    return {"id": rid or m.id, "mid": m.id, "from": s.display, "from_id": s.id, "from_address": s.address,
            "from_avatar": s.avatar.url if s.avatar else "", "subject": m.subject, "body": m.body,
            "date": timezone.localtime(m.created_at).strftime("%d/%m/%Y %H:%M"), "ts": timezone.localtime(m.created_at).isoformat(), "to": to, "attachments": _atts(m),
            "is_read": r.is_read if r else True, "starred": r.is_starred if r else False, "archived": r.is_archived if r else False}

def _draft_info(m):
    d = m.draft_data or {}
    us = User.objects.filter(id__in=d.get("user_ids") or [])
    return {"to": [{"id": u.id, "name": u.display} for u in us], "broadcast": bool(d.get("broadcast")), "levels": d.get("levels") or [],
            "parcours": d.get("parcours") or [], "include_teachers": bool(d.get("include_teachers")), "email_copy": bool(d.get("email_copy"))}

BOXES = {"inbox": dict(is_deleted=False, is_archived=False), "starred": dict(is_deleted=False, is_starred=True),
         "archive": dict(is_deleted=False, is_archived=True), "trash": dict(is_deleted=True)}

@api_view(["GET"])
def box(request, name):
    u, q = request.user, request.GET.get("q", "").strip()
    if name in ("sent", "drafts"):
        ms = Message.objects.filter(sender=u, is_draft=(name == "drafts"), sender_deleted=False).select_related("sender").prefetch_related("recipients__user", "attachments").order_by("-created_at")
        if q: ms = ms.filter(Q(subject__icontains=q) | Q(body__icontains=q))
        out = []
        for m in ms[:200]:
            if name == "drafts":
                info = _draft_info(m)
                c = card(m, to=", ".join(x["name"] for x in info["to"]) or ("Groupe" if info["broadcast"] else "(aucun destinataire)"))
                c["draft"] = info
            else:
                names = [r.user.display for r in m.recipients.all()]
                c = card(m, to=", ".join(names[:3]) + (" +%d autres" % (len(names) - 3) if len(names) > 3 else ""))
            out.append(c)
        return Response(out)
    if name not in BOXES: return Response({"error": "Boite inconnue"}, status=404)
    rs = Recipient.objects.filter(user=u, purged=False, message__is_draft=False, **BOXES[name]).select_related("message__sender").prefetch_related("message__attachments").order_by("-message__created_at")
    if q: rs = rs.filter(Q(message__subject__icontains=q) | Q(message__body__icontains=q) | Q(message__sender__first_name__icontains=q))
    return Response([card(r.message, r.id, r, "moi") for r in rs[:200]])

def _can_access(user, m):
    return m.sender_id == user.id or Recipient.objects.filter(message=m, user=user, purged=False).exists()

def _targets(u, p):
    t = set(User.objects.filter(id__in=p.get("user_ids") or [], is_approved=True, is_active=True))
    if p.get("broadcast"):
        if not Role.objects.filter(code=u.role, can_broadcast=True).exists(): raise PermissionDenied("Envoi groupe non autorise pour votre role")
        qs = User.objects.filter(role__in=list(Role.objects.filter(has_academic=True).values_list("code", flat=True)), is_active=True, is_approved=True)
        if p.get("levels"): qs = qs.filter(level__in=p["levels"])
        if p.get("parcours"): qs = qs.filter(parcours__in=p["parcours"])
        t |= set(qs)
        if p.get("include_teachers") and u.role == "admin":
            others = list(Role.objects.filter(has_academic=False).exclude(code="admin").values_list("code", flat=True))
            t |= set(User.objects.filter(role__in=others, is_approved=True, is_active=True))
    t.discard(u)
    return t

@api_view(["POST"])
def send(request):
    u = request.user
    try: p = json.loads(request.data.get("payload") or "{}")
    except ValueError: return Response({"error": "Requete invalide"}, status=400)
    files = request.FILES.getlist("files")
    if len(files) > MAX_FILES: return Response({"error": "10 pieces jointes maximum"}, status=400)
    for f in files:
        if f.size > MAX_FILE: return Response({"error": "%s depasse 10 Mo" % f.name}, status=400)
        if f.name.lower().endswith(BLOCKED): return Response({"error": "Type de fichier interdit : " + f.name}, status=400)
    subject, body = (p.get("subject") or "").strip()[:200], (p.get("body") or "").strip()
    draft = Message.objects.filter(pk=p["draft_id"], sender=u, is_draft=True).first() if p.get("draft_id") else None
    data = {k: p.get(k) for k in ("user_ids", "broadcast", "levels", "parcours", "include_teachers", "email_copy")}
    save_draft, targets = bool(p.get("save_draft")), set()
    if not save_draft:
        if not subject or not body: return Response({"error": "Objet et message requis"}, status=400)
        targets = _targets(u, p)
        if not targets: return Response({"error": "Aucun destinataire"}, status=400)
    if draft:
        msg = draft
        msg.subject, msg.body = subject, body
        if save_draft: msg.draft_data = data
        else: msg.is_draft, msg.draft_data, msg.created_at = False, {}, timezone.now()
        msg.save()
        msg.attachments.exclude(id__in=p.get("keep_ids") or []).delete()
    else:
        msg = Message.objects.create(sender=u, subject=subject, body=body, is_draft=save_draft, draft_data=data if save_draft else {})
        for a in Attachment.objects.filter(id__in=p.get("keep_ids") or []).select_related("message"):
            if _can_access(u, a.message): Attachment.objects.create(message=msg, file=a.file.name, name=a.name, size=a.size)
    for f in files: Attachment.objects.create(message=msg, file=f, name=f.name[:255], size=f.size)
    if save_draft:
        return Response({"draft_id": msg.id, "attachments": _atts(msg)})
    Recipient.objects.bulk_create([Recipient(message=msg, user=t) for t in targets])
    notify(targets, u, subject, body if p.get("email_copy") else None, msg.attachments.count())
    return Response({"sent_to": len(targets)}, status=201)

ACTIONS = {"read": {"is_read": True}, "unread": {"is_read": False}, "star": {"is_starred": True}, "unstar": {"is_starred": False},
           "archive": {"is_archived": True}, "unarchive": {"is_archived": False}, "trash": {"is_deleted": True},
           "restore": {"is_deleted": False}, "purge": {"purged": True}}

@api_view(["POST"])
def action(request, pk):
    a = request.data.get("action")
    if a not in ACTIONS: return Response({"error": "Action inconnue"}, status=400)
    Recipient.objects.filter(pk=pk, user=request.user).update(**ACTIONS[a])
    return Response({"ok": True})

@api_view(["POST"])
def bulk(request):
    d = request.data
    try: ids = [int(i) for i in (d.get("ids") or [])][:500]
    except (TypeError, ValueError): return Response({"error": "Requete invalide"}, status=400)
    a = d.get("action")
    if a == "delete_sent":
        Message.objects.filter(pk__in=ids, sender=request.user, is_draft=True).delete()
        Message.objects.filter(pk__in=ids, sender=request.user, is_draft=False).update(sender_deleted=True)
    elif a in ACTIONS:
        Recipient.objects.filter(pk__in=ids, user=request.user).update(**ACTIONS[a])
    else:
        return Response({"error": "Action inconnue"}, status=400)
    return Response({"ok": True})

@api_view(["POST"])
def msg_delete(request, pk):
    m = Message.objects.filter(pk=pk, sender=request.user).first()
    if not m: return Response({"error": "Introuvable"}, status=404)
    if m.is_draft: m.delete()
    else: m.sender_deleted = True; m.save(update_fields=["sender_deleted"])
    return Response({"ok": True})

@api_view(["POST"])
def empty_trash(request):
    Recipient.objects.filter(user=request.user, is_deleted=True, purged=False).update(purged=True)
    return Response({"ok": True})

@api_view(["GET"])
def download(request, pk):
    a = Attachment.objects.select_related("message").filter(pk=pk).first()
    if not a or not _can_access(request.user, a.message): return Response({"error": "Introuvable"}, status=404)
    return FileResponse(a.file.open("rb"), as_attachment=True, filename=a.name)

@api_view(["GET"])
def stats(request):
    u = request.user
    r = Recipient.objects.filter(user=u, purged=False, message__is_draft=False)
    out = {"unread": r.filter(is_read=False, is_deleted=False, is_archived=False).count(), "inbox": r.filter(is_deleted=False, is_archived=False).count(),
           "sent": Message.objects.filter(sender=u, is_draft=False, sender_deleted=False).count(),
           "drafts": Message.objects.filter(sender=u, is_draft=True).count()}
    if u.role == "admin":
        out.update({"students": User.objects.filter(role__in=list(Role.objects.filter(has_academic=True).values_list("code", flat=True))).count(),
                    "teachers": User.objects.filter(role="teacher", is_approved=True).count(),
                    "pending": User.objects.filter(is_approved=False).count(), "messages": Message.objects.filter(is_draft=False).count()})
    return Response(out)
