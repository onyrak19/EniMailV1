import { useState, useEffect, useCallback, useRef } from "react";

const LEVELS = ["L1", "L2", "L3", "M1", "M2"];
const PARCOURS = ["IG", "GB", "ASR", "MDI"];
const ROLE = { admin: "Administrateur", teacher: "Professeur", student: "Étudiant" };
const who = (u) => (u.role === "student" ? [u.level, u.parcours].filter(Boolean).join(" ") : ROLE[u.role]);
const TITLES = { inbox: "Boîte de réception", starred: "Favoris", sent: "Messages envoyés", drafts: "Brouillons", archive: "Archives", trash: "Corbeille" };
const enc = encodeURIComponent;
const isMobile = () => window.innerWidth < 800;

const api = async (path, method = "GET", body) => {
  const t = localStorage.getItem("token"), fd = body instanceof FormData;
  try {
    const r = await fetch("/api/" + path, { method, headers: { ...(t ? { Authorization: "Bearer " + t } : {}), ...(fd ? {} : { "Content-Type": "application/json" }) }, body: body ? (fd ? body : JSON.stringify(body)) : undefined });
    let data = {}; try { data = await r.json(); } catch {}
    if (r.status === 401 && t && path !== "login/") { localStorage.removeItem("token"); location.reload(); }
    return { ok: r.ok, status: r.status, data };
  } catch { return { ok: false, status: 0, data: { error: "Serveur injoignable" } }; }
};
const err = (d) => d.detail || d.error || "Erreur";
const fmt = (n) => (n > 1048576 ? (n / 1048576).toFixed(1) + " Mo" : Math.max(1, Math.round(n / 1024)) + " Ko");
const short = (m) => {
  const d = new Date(m.ts), n = new Date();
  if (d.toDateString() === n.toDateString()) return d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
  return d.getFullYear() === n.getFullYear() ? d.toLocaleDateString("fr-FR", { day: "numeric", month: "short" }) : d.toLocaleDateString("fr-FR");
};
const download = async (a) => {
  const r = await fetch("/api/attachment/" + a.id + "/", { headers: { Authorization: "Bearer " + localStorage.getItem("token") } });
  if (!r.ok) return alert("Téléchargement impossible");
  const url = URL.createObjectURL(await r.blob()), l = document.createElement("a");
  l.href = url; l.download = a.name; l.click(); URL.revokeObjectURL(url);
};
const Av = ({ src, name, size = 38 }) => src
  ? <img className="av" src={src} alt="" style={{ width: size, height: size }} />
  : <span className="av" style={{ width: size, height: size, fontSize: size * 0.45 }}>{(name || "?")[0].toUpperCase()}</span>;

function Count({ to }) {
  const [n, setN] = useState(0);
  useEffect(() => {
    if (to == null) return;
    let id, s = null; const from = n;
    const step = (t) => { s = s == null ? t : s; const p = Math.min((t - s) / 700, 1); setN(Math.round(from + (to - from) * p)); if (p < 1) id = requestAnimationFrame(step); };
    id = requestAnimationFrame(step); return () => cancelAnimationFrame(id);
  }, [to]);
  return to == null ? "-" : n;
}

function Auth({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [f, setF] = useState({ email: "", login: "", username: "", password: "", name: "", role: "student", level: "L1", parcours: "IG", code: "" });
  const [sent, setSent] = useState(false), [msg, setMsg] = useState(""), [bad, setBad] = useState(false), [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const say = (m, b = false) => { setMsg(m); setBad(b); };
  const go = (m) => { setMode(m); setSent(false); say(""); };
  const login = async () => {
    setBusy(true); const r = await api("login/", "POST", { username: f.login, password: f.password }); setBusy(false);
    if (r.ok) { localStorage.setItem("token", r.data.access); onLogin(r.data.user); } else say(r.status === 403 ? err(r.data) : "Identifiants incorrects", true);
  };
  const sendCode = async () => {
    setBusy(true); say("Envoi du code...");
    const r = mode === "forgot" ? await api("password/code/", "POST", { identifier: f.login }) : await api("register/code/", "POST", { email: f.email });
    setBusy(false);
    if (r.ok) { setSent(true); say(r.data.warning ? "⚠ " + r.data.warning : mode === "forgot" ? "Si le compte existe, un code a été envoyé à son adresse e-mail (vérifiez les spams)." : "Code envoyé à " + f.email + " (vérifiez aussi les spams)"); } else say(err(r.data), true);
  };
  const register = async () => {
    const r = await api("register/", "POST", f);
    if (r.ok) { go("login"); say("Compte créé ! Votre adresse ENI Mail : " + r.data.address + (r.data.pending ? " — un administrateur doit valider votre compte professeur." : " — connectez-vous.")); } else say(err(r.data), true);
  };
  const reset = async () => {
    const r = await api("password/reset/", "POST", { identifier: f.login, code: f.code, password: f.password });
    if (r.ok) { go("login"); say("Mot de passe modifié, connectez-vous."); } else say(err(r.data), true);
  };
  return (
    <div className="auth glass">
      <img src="/logo.png" className="biglogo" alt="ENI" /><div className="logo">ENI MAIL</div>
      <h2 style={{ textAlign: "center", fontSize: 18 }}>{mode === "login" ? "Connexion" : mode === "register" ? "Inscription" : "Mot de passe oublié"}</h2>
      {mode !== "forgot" && <div className="tabs"><button className={mode === "login" ? "on" : ""} onClick={() => go("login")}>Connexion</button>
        <button className={mode === "register" ? "on" : ""} onClick={() => go("register")}>Inscription</button></div>}
      {mode === "register"
        ? <input type="email" placeholder="Adresse e-mail personnelle (Gmail)" value={f.email} onChange={set("email")} disabled={sent} />
        : <input placeholder="Nom d'utilisateur ou adresse ENI Mail" value={f.login} onChange={set("login")} disabled={sent} autoCapitalize="none" />}
      {mode === "login" && <><input type="password" placeholder="Mot de passe" value={f.password} onChange={set("password")} onKeyDown={(e) => e.key === "Enter" && login()} />
        <button className="pri" disabled={busy} onClick={login}>Se connecter</button>{" "}<button className="link" onClick={() => go("forgot")}>Mot de passe oublié ?</button></>}
      {mode !== "login" && !sent && <button className="pri" disabled={busy || !(mode === "register" ? f.email : f.login)} onClick={sendCode}>Recevoir le code de vérification</button>}
      {mode === "register" && sent && <>
        <input placeholder="Code à 6 chiffres reçu par e-mail" value={f.code} onChange={set("code")} maxLength={6} inputMode="numeric" />
        <input placeholder="Nom d'utilisateur (lettres, chiffres, . _ -)" value={f.username} onChange={set("username")} autoCapitalize="none" />
        {f.username && <small>Votre adresse ENI Mail sera : <b style={{ color: "#fff" }}>{f.username.toLowerCase()}@enimail.com</b></small>}
        <input placeholder="Nom complet" value={f.name} onChange={set("name")} />
        <input type="password" placeholder="Mot de passe (6 caractères min.)" value={f.password} onChange={set("password")} />
        <select value={f.role} onChange={set("role")}><option value="student">Je suis étudiant</option><option value="teacher">Je suis professeur</option></select>
        {f.role === "student" && <div className="row"><select value={f.level} onChange={set("level")}>{LEVELS.map((l) => <option key={l}>{l}</option>)}</select>
          <select value={f.parcours} onChange={set("parcours")}>{PARCOURS.map((p) => <option key={p}>{p}</option>)}</select></div>}
        {f.role === "teacher" && <p className="dim">Votre compte devra être validé par l'administrateur.</p>}
        <button className="pri" onClick={register}>Créer mon compte</button></>}
      {mode === "forgot" && sent && <>
        <input placeholder="Code à 6 chiffres reçu par e-mail" value={f.code} onChange={set("code")} maxLength={6} inputMode="numeric" />
        <input type="password" placeholder="Nouveau mot de passe (6 caractères min.)" value={f.password} onChange={set("password")} />
        <button className="pri" onClick={reset}>Changer le mot de passe</button></>}
      {mode === "forgot" && <p><button className="link" onClick={() => go("login")}>← Retour à la connexion</button></p>}
      <p key={msg} className={"msg" + (bad ? " bad shake" : "")}>{msg}</p>
    </div>
  );
}

function Home({ me, stats, flash, openCompose, go }) {
  const list = [[stats.unread, "Non lus"], [stats.inbox, "Reçus"], [stats.sent, "Envoyés"], [stats.drafts, "Brouillons"]];
  if (me.role === "admin") list.push([stats.students, "Étudiants"], [stats.teachers, "Professeurs"], [stats.pending, "À valider"], [stats.messages, "Messages total"]);
  return (<div className="panel pad"><h2 style={{ marginTop: 0 }}>Bienvenue, {me.name}</h2><p className="dim">{who(me)}</p>
    <p>Votre adresse ENI Mail :</p><span className="addr">{me.address}</span>{" "}
    <button className="link" onClick={() => { navigator.clipboard && navigator.clipboard.writeText(me.address); flash("Adresse copiée"); }}>Copier</button>
    <p className="dim">Donnez cette adresse (ou votre nom d'utilisateur) pour recevoir des messages. Les alertes arrivent aussi sur {me.email}.</p>
    <p style={{ display: "flex", gap: 10, flexWrap: "wrap" }}><button className="pri" onClick={() => openCompose()}>✎ Nouveau message</button><button onClick={() => go("dir")}>👥 Rechercher un utilisateur</button></p>
    <div className="cards">{list.map(([n, l], i) => <div className="stat glass" key={l} style={{ "--i": i }}><b><Count to={n} /></b>{l}</div>)}</div></div>);
}

function Directory({ onWrite }) {
  const [q, setQ] = useState(""), [role, setRole] = useState(""), [lv, setLv] = useState(""), [pc, setPc] = useState(""), [list, setList] = useState([]), [loading, setLoading] = useState(true);
  useEffect(() => {
    setLoading(true);
    const t = setTimeout(() => api("users/?full=1&q=" + enc(q) + "&role=" + role + "&level=" + lv + "&parcours=" + pc).then((r) => { if (r.ok) setList(r.data); setLoading(false); }), 220);
    return () => clearTimeout(t);
  }, [q, role, lv, pc]);
  const reset = () => { setQ(""); setRole(""); setLv(""); setPc(""); };
  return (<div className="panel"><div className="lhead"><h3>Annuaire</h3><span className="dim">{loading ? "Recherche..." : list.length + " résultat(s)"}</span>
    {(q || role || lv || pc) && <button className="link" onClick={reset}>Effacer les filtres</button>}</div>
    <div style={{ padding: "12px 16px 0" }}><input autoFocus placeholder="🔍 Nom, nom d'utilisateur, e-mail exact ou adresse @enimail.com" value={q} onChange={(e) => setQ(e.target.value)} /></div>
    <div className="filters"><select value={role} onChange={(e) => setRole(e.target.value)}><option value="">Tous les rôles</option><option value="student">Étudiants</option><option value="teacher">Professeurs</option><option value="admin">Administrateurs</option></select>
      <select value={lv} onChange={(e) => setLv(e.target.value)}><option value="">Tous niveaux</option>{LEVELS.map((l) => <option key={l}>{l}</option>)}</select>
      <select value={pc} onChange={(e) => setPc(e.target.value)}><option value="">Tous parcours</option>{PARCOURS.map((p) => <option key={p}>{p}</option>)}</select></div>
    {loading && list.length === 0 && [1, 2, 3].map((i) => <div key={i} className="skel" />)}
    {!loading && list.length === 0 && <p className="pad dim">Aucun utilisateur trouvé.</p>}
    <div className="dgrid">{list.map((u, i) => <div key={u.id} className="ucard glass" style={{ "--i": Math.min(i, 14) }}>
      <Av src={u.avatar} name={u.name} size={52} /><div className="ub"><b>{u.name}</b><span className="mono">{u.address}</span><span className="tag">{who(u)}</span></div>
      <button className="pri" onClick={() => onWrite(u)}>✎</button></div>)}</div></div>);
}

function List({ kind, q, nav, refresh, tick }) {
  const [items, setItems] = useState([]), [open, setOpen] = useState(null), [loading, setLoading] = useState(true);
  const [sel, setSel] = useState([]), [gone, setGone] = useState([]), [flt, setFlt] = useState("all");
  const load = useCallback(() => api("box/" + kind + "/?q=" + enc(q)).then((r) => { if (r.ok) setItems(r.data); setLoading(false); }), [kind, q]);
  useEffect(() => { load(); }, [load, tick]);
  const out = kind === "sent" || kind === "drafts";
  const cur = items.find((i) => i.id === open);
  const shown = items.filter((m) => (flt === "unread" ? !m.is_read : flt === "att" ? m.attachments.length > 0 : true));
  const leaves = (a) => (kind === "inbox" && ["archive", "trash"].includes(a)) || (kind === "archive" && ["unarchive", "trash"].includes(a)) ||
    (kind === "starred" && ["trash", "unstar"].includes(a)) || (kind === "trash" && ["restore", "purge"].includes(a));
  const vanish = (ids, run) => { setGone((g) => [...g, ...ids]); setTimeout(async () => { await run(); setGone([]); setSel([]); setOpen(null); await load(); refresh(); }, 260); };
  const act = (m, a, keep) => {
    const run = () => api("action/" + m.id + "/", "POST", { action: a });
    if (leaves(a)) vanish([m.id], run); else run().then(() => { if (!keep) setOpen(null); load(); refresh(); });
  };
  const rm = (m) => { if (confirm(kind === "drafts" ? "Supprimer ce brouillon ?" : "Supprimer ce message de vos envoyés ? Les destinataires le conservent.")) vanish([m.id], () => api("delete/" + m.mid + "/", "POST")); };
  const purge = (m) => { if (confirm("Supprimer définitivement ce message ?")) act(m, "purge"); };
  const emptyTrash = async () => { if (confirm("Vider la corbeille définitivement ?")) { await api("trash/empty/", "POST"); load(); refresh(); } };
  const bulk = (a) => {
    if (a === "purge" && !confirm("Supprimer définitivement " + sel.length + " message(s) ?")) return;
    if (a === "delete_sent" && !confirm("Supprimer " + sel.length + " message(s) de cette liste ?")) return;
    const run = () => api("bulk/", "POST", { ids: sel, action: a });
    if (a === "delete_sent" || leaves(a)) vanish(sel, run); else run().then(() => { setSel([]); load(); refresh(); });
  };
  const toggle = (id) => setSel((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));
  const show = (m) => { if (kind === "drafts") return nav.draft(m); setOpen(m.id); if (!out && !m.is_read) act(m, "read", true); };
  const stop = (fn) => (e) => { e.stopPropagation(); fn(); };
  if (cur) return (
    <div className="panel pad slidein">
      <div className="toolbar"><button onClick={() => setOpen(null)}>← Retour</button>
        {!out && kind !== "trash" && <>
          <button onClick={() => act(cur, cur.archived ? "unarchive" : "archive")}>{cur.archived ? "Désarchiver" : "🗄 Archiver"}</button>
          <button onClick={() => act(cur, "unread")}>Marquer non lu</button>
          <button onClick={() => act(cur, cur.starred ? "unstar" : "star", true)}>{cur.starred ? "★ Retirer des favoris" : "☆ Favori"}</button>
          <button className="danger" onClick={() => act(cur, "trash")}>🗑 Supprimer</button></>}
        {kind === "trash" && <><button onClick={() => act(cur, "restore")}>Restaurer</button><button className="danger" onClick={() => purge(cur)}>Supprimer définitivement</button></>}
        {kind === "sent" && <button className="danger" onClick={() => rm(cur)}>🗑 Supprimer</button>}</div>
      <h2 style={{ margin: "0 0 6px", overflowWrap: "anywhere" }}>{cur.subject || "(sans objet)"}</h2>
      <div className="from"><Av src={cur.from_avatar} name={cur.from} size={44} /><div style={{ minWidth: 0 }}><b>{cur.from}</b> <small>&lt;{cur.from_address}&gt;</small><br /><small>À : {cur.to} · {cur.date}</small></div></div>
      <div className="body">{cur.body}</div>
      {cur.attachments.length > 0 && <div className="atts">{cur.attachments.map((a) => <span key={a.id} className="att" onClick={() => download(a)}>📎 {a.name} <small>({fmt(a.size)})</small></span>)}</div>}
      <div style={{ marginTop: 16 }}>{!out && <button className="pri" onClick={() => nav.reply(cur)}>↩ Répondre</button>}{" "}<button onClick={() => nav.forward(cur)}>➦ Transférer</button></div>
    </div>);
  return (<div className="panel">
    {sel.length > 0
      ? <div className="lhead bulk"><b>{sel.length} sélectionné(s)</b>
          {!out && kind !== "trash" && <><button onClick={() => bulk("archive")}>🗄 Archiver</button><button onClick={() => bulk("read")}>Lu</button><button onClick={() => bulk("unread")}>Non lu</button><button className="danger" onClick={() => bulk("trash")}>🗑 Supprimer</button></>}
          {kind === "trash" && <><button onClick={() => bulk("restore")}>Restaurer</button><button className="danger" onClick={() => bulk("purge")}>Supprimer définitivement</button></>}
          {out && <button className="danger" onClick={() => bulk("delete_sent")}>🗑 Supprimer</button>}
          <button className="link" onClick={() => setSel([])}>Annuler</button></div>
      : <div className="lhead"><input type="checkbox" title="Tout sélectionner" checked={false} onChange={() => setSel(shown.map((m) => m.id))} />
          <h3>{TITLES[kind]}</h3><span className="dim">{shown.length} message(s)</span>
          {kind === "trash" && items.length > 0 && <button className="danger" onClick={emptyTrash}>Vider la corbeille</button>}
          <button className="iconbtn" title="Actualiser" onClick={load}>⟳</button></div>}
    {!out && <div className="fchips">{[["all", "Tous"], ["unread", "Non lus"], ["att", "📎 Pièces jointes"]].map(([k, l]) => <span key={k} className={"chip" + (flt === k ? " on" : "")} onClick={() => setFlt(k)}>{l}</span>)}</div>}
    {loading && [1, 2, 3, 4, 5].map((i) => <div key={i} className="skel" />)}
    {!loading && shown.length === 0 && <p className="pad dim">Aucun message.</p>}
    {shown.map((m, i) => (
      <div key={m.id} className={"mrow" + (!out && !m.is_read ? " unread" : "") + (gone.includes(m.id) ? " gone" : "") + (sel.includes(m.id) ? " sel" : "")} style={{ "--i": Math.min(i, 12) }} onClick={() => show(m)}>
        <input type="checkbox" className="chk" checked={sel.includes(m.id)} onClick={(e) => e.stopPropagation()} onChange={() => toggle(m.id)} />
        {out ? <span className="mstar" /> : <span className={"star mstar" + (m.starred ? " on" : "")} onClick={stop(() => act(m, m.starred ? "unstar" : "star", true))}>{m.starred ? "★" : "☆"}</span>}
        <Av src={out ? "" : m.from_avatar} name={out ? m.to : m.from} size={30} />
        <span className="who">{out ? "À : " + m.to : m.from}</span>
        <span className="mid"><span className="sub">{m.subject || "(sans objet)"}</span><span className="snip"> — {m.attachments.length > 0 && "📎 "}{m.body.slice(0, 100)}</span></span>
        <small className="mdate">{short(m)}</small>
        <span className="racts">
          {!out && kind !== "trash" && <><button className="iconbtn" title="Archiver" onClick={stop(() => act(m, m.archived ? "unarchive" : "archive"))}>🗄</button><button className="iconbtn" title="Supprimer" onClick={stop(() => act(m, "trash"))}>🗑</button></>}
          {kind === "trash" && <><button className="iconbtn" title="Restaurer" onClick={stop(() => act(m, "restore"))}>↩</button><button className="iconbtn" title="Supprimer définitivement" onClick={stop(() => purge(m))}>✕</button></>}
          {out && <button className="iconbtn" title="Supprimer" onClick={stop(() => rm(m))}>🗑</button>}</span>
      </div>))}
  </div>);
}

function ToField({ to, setTo, touch }) {
  const [val, setVal] = useState(""), [sug, setSug] = useState([]), [e, setE] = useState("");
  useEffect(() => {
    const v = val.trim(); if (!v) { setSug([]); return; }
    const t = setTimeout(() => api("users/?q=" + enc(v)).then((r) => r.ok && setSug(r.data.filter((u) => !to.find((x) => x.id === u.id)))), 150);
    return () => clearTimeout(t);
  }, [val, to]);
  const add = (u) => { if (!to.find((x) => x.id === u.id)) setTo([...to, u]); setVal(""); setSug([]); setE(""); touch(); };
  const commit = async () => {
    const v = val.trim().replace(/[,;]+$/, ""); if (!v) return;
    const r = await api("users/resolve/?v=" + enc(v));
    if (r.ok) add(r.data); else if (sug.length === 1) add(sug[0]); else setE("Aucun utilisateur « " + v + " »");
  };
  const key = (ev) => {
    if (["Enter", ",", ";", "Tab"].includes(ev.key) && val.trim()) { ev.preventDefault(); commit(); }
    else if (ev.key === "Backspace" && !val && to.length) { setTo(to.slice(0, -1)); touch(); }
  };
  return (<>{to.map((u) => <span key={u.id} className="chip on" title={u.address} onClick={() => { setTo(to.filter((x) => x.id !== u.id)); touch(); }}>{u.name} ✕</span>)}
    <input placeholder="Nom d'utilisateur, adresse ou e-mail" value={val} autoCapitalize="none" onChange={(ev) => { setVal(ev.target.value); setE(""); }} onKeyDown={key} onBlur={commit} />
    {e && <small style={{ color: "var(--red2)", width: "100%" }}>{e}</small>}
    {sug.length > 0 && <div className="sug">{sug.map((u) => <div key={u.id} onMouseDown={(ev) => { ev.preventDefault(); add(u); }}>
      <Av src={u.avatar} name={u.name} size={30} /><span><b>{u.name}</b> <small>{u.address} · {who(u)}</small></span></div>)}</div>}</>);
}

function Compose({ me, cw, setCw, close, refresh, onSent, flash }) {
  const d = cw.draft || {};
  const [to, setTo] = useState(d.to || []), [lv, setLv] = useState(d.levels || []), [pc, setPc] = useState(d.parcours || []);
  const [bc, setBc] = useState(!!d.broadcast), [it, setIt] = useState(!!d.include_teachers);
  const [subject, setSubject] = useState(d.subject || ""), [body, setBody] = useState(d.body || ""), [msg, setMsg] = useState("");
  const [files, setFiles] = useState([]), [keep, setKeep] = useState(d.keep || []), [did, setDid] = useState(d.draft_id || null);
  const [busy, setBusy] = useState(false), [dirty, setDirty] = useState(false);
  const touch = () => setDirty(true);
  const tog = (a, s, v) => { s(a.includes(v) ? a.filter((x) => x !== v) : [...a, v]); touch(); };
  const submit = async (asDraft) => {
    setBusy(true);
    const fd = new FormData();
    fd.append("payload", JSON.stringify({ subject, body, user_ids: to.map((u) => u.id), broadcast: bc, levels: lv, parcours: pc, include_teachers: it, draft_id: did, keep_ids: keep.map((a) => a.id), save_draft: asDraft }));
    files.forEach((f) => fd.append("files", f));
    const r = await api("send/", "POST", fd); setBusy(false);
    if (!r.ok) { setMsg("✖ " + err(r.data)); return r; }
    if (asDraft) { setDid(r.data.draft_id); setKeep(r.data.attachments); setFiles([]); setDirty(false); setMsg("✔ Brouillon enregistré"); refresh(); }
    else onSent(r.data.sent_to);
    return r;
  };
  const shut = async () => { if (dirty) { const r = await submit(true); if (!r.ok) return; flash("Brouillon enregistré"); } close(); };
  const discard = async () => { if (did) await api("delete/" + did + "/", "POST"); refresh(); close(); };
  const mm = (p) => (e) => { e.stopPropagation(); setCw({ ...cw, ...p }); };
  return (<div className={"cw" + (cw.max ? " max" : "") + (cw.full ? " full" : "") + (cw.min ? " min" : "")}>
    <div className="cw-head" onClick={() => cw.min && setCw({ ...cw, min: false })}><b>{subject || "Nouveau message"}</b>
      <button title="Réduire" onClick={mm({ min: !cw.min })}>—</button>
      <button className="desk" title="Agrandir (fenêtre)" onClick={mm({ max: !cw.max, full: false, min: false })}>⤢</button>
      <button className="desk" title="Plein écran" onClick={mm({ full: !cw.full, max: false, min: false })}>⛶</button>
      <button title="Fermer (enregistre un brouillon)" onClick={(e) => { e.stopPropagation(); shut(); }}>✕</button></div>
    {!cw.min && <><div className="cw-body">
      <div className="cw-row"><span className="lbl">À</span><ToField to={to} setTo={setTo} touch={touch} />
        {me.role !== "student" && <button className="link" onClick={() => { setBc(!bc); touch(); }}>{bc ? "✔ " : ""}👥 Groupe</button>}</div>
      {bc && <div className="cw-row" style={{ display: "block" }}><small>Envoi groupe aux étudiants (aucun filtre = tous)</small>
        <div>Niveaux : {LEVELS.map((l) => <span key={l} className={"chip" + (lv.includes(l) ? " on" : "")} onClick={() => tog(lv, setLv, l)}>{l}</span>)}</div>
        <div>Parcours : {PARCOURS.map((p) => <span key={p} className={"chip" + (pc.includes(p) ? " on" : "")} onClick={() => tog(pc, setPc, p)}>{p}</span>)}</div>
        {me.role === "admin" && <label><input type="checkbox" checked={it} onChange={(e) => { setIt(e.target.checked); touch(); }} />Inclure aussi tous les professeurs</label>}</div>}
      <div className="cw-row"><input placeholder="Objet" value={subject} onChange={(e) => { setSubject(e.target.value); touch(); }} /></div>
      <textarea placeholder="Rédigez votre message..." value={body} onChange={(e) => { setBody(e.target.value); touch(); }} onKeyDown={(e) => { if ((e.ctrlKey || e.metaKey) && e.key === "Enter") submit(false); }} />
      <div className="files">{keep.map((a) => <span key={"k" + a.id} className="att" onClick={() => { setKeep(keep.filter((x) => x.id !== a.id)); touch(); }}>📎 {a.name} ✕</span>)}
        {files.map((f, i) => <span key={i} className="att" onClick={() => { setFiles(files.filter((_, j) => j !== i)); touch(); }}>📎 {f.name} ({fmt(f.size)}) ✕</span>)}</div></div>
      <div className="cw-foot"><button className="pri" disabled={busy} onClick={() => submit(false)}>Envoyer ➤</button>
        <label className="filebtn iconbtn" title="Joindre des fichiers" style={{ cursor: "pointer" }}>📎<input type="file" multiple onChange={(e) => { setFiles([...files, ...e.target.files]); e.target.value = ""; touch(); }} /></label>
        <button className="iconbtn" title="Enregistrer le brouillon" disabled={busy} onClick={() => submit(true)}>💾</button>
        <span className="msg" style={{ flex: 1, minHeight: 0, fontSize: 14 }}>{msg}</span>
        <button className="iconbtn" title="Supprimer le brouillon" onClick={discard}>🗑</button></div></>}
  </div>);
}

function UserForm({ u, onDone }) {
  const [f, setF] = useState(u ? { name: u.name, username: u.username, email: u.email, role: u.role, level: u.level || "L1", parcours: u.parcours || "IG", password: "" }
    : { name: "", username: "", email: "", role: "student", level: "L1", parcours: "IG", password: "" });
  const [msg, setMsg] = useState("");
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const save = async () => {
    const body = { ...f }; if (u && !body.password) delete body.password;
    const r = u ? await api("admin/users/" + u.id + "/", "PATCH", body) : await api("admin/users/", "POST", body);
    r.ok ? onDone() : setMsg("✖ " + err(r.data));
  };
  return (<div className="panel pad" style={{ maxWidth: 540 }}><h3>{u ? "Modifier l'utilisateur" : "Nouvel utilisateur"}</h3>
    <input placeholder="Nom complet" value={f.name} onChange={set("name")} /><input placeholder="Nom d'utilisateur" value={f.username} onChange={set("username")} autoCapitalize="none" />
    {f.username && <small>Adresse ENI Mail : {f.username.toLowerCase()}@enimail.com</small>}
    <input type="email" placeholder="E-mail personnel (alertes)" value={f.email} onChange={set("email")} />
    <input type="password" placeholder={u ? "Nouveau mot de passe (laisser vide pour ne pas changer)" : "Mot de passe (6 caractères min.)"} value={f.password} onChange={set("password")} />
    <select value={f.role} onChange={set("role")}><option value="student">Étudiant</option><option value="teacher">Professeur</option><option value="admin">Administrateur</option></select>
    {f.role === "student" && <div className="row"><select value={f.level} onChange={set("level")}>{LEVELS.map((l) => <option key={l}>{l}</option>)}</select>
      <select value={f.parcours} onChange={set("parcours")}>{PARCOURS.map((p) => <option key={p}>{p}</option>)}</select></div>}
    <p><button className="pri" onClick={save}>Enregistrer</button>{" "}<button onClick={() => onDone()}>Annuler</button> <span className="msg bad">{msg}</span></p></div>);
}

function Users() {
  const [list, setList] = useState([]), [q, setQ] = useState(""), [role, setRole] = useState(""), [edit, setEdit] = useState(null), [msg, setMsg] = useState("");
  const load = useCallback(() => api("admin/users/?q=" + enc(q) + "&role=" + role).then((r) => r.ok && setList(r.data)), [q, role]);
  useEffect(() => { load(); }, [load]);
  const toggle = async (u) => { const r = await api("admin/users/" + u.id + "/", "PATCH", { is_active: !u.active }); r.ok ? load() : setMsg(err(r.data)); };
  const remove = async (u) => { if (!confirm("Supprimer " + u.name + " et tous ses messages ?")) return; const r = await api("admin/users/" + u.id + "/", "DELETE"); r.ok ? load() : setMsg(err(r.data)); };
  if (edit) return <UserForm u={edit === "new" ? null : edit} onDone={() => { setEdit(null); load(); }} />;
  return (<div><div className="row" style={{ marginBottom: 10, flexWrap: "wrap" }}><input placeholder="🔍 Rechercher (nom, utilisateur, e-mail)..." value={q} onChange={(e) => setQ(e.target.value)} />
    <select value={role} onChange={(e) => setRole(e.target.value)}><option value="">Tous les rôles</option><option value="student">Étudiants</option><option value="teacher">Professeurs</option><option value="admin">Administrateurs</option></select>
    <button className="pri" onClick={() => setEdit("new")}>+ Nouvel utilisateur</button></div><p className="msg bad">{msg}</p>
    <div className="panel pad" style={{ overflowX: "auto" }}><table><thead><tr><th></th><th>Nom</th><th>Adresse ENI Mail</th><th>E-mail personnel</th><th>Rôle</th><th>Statut</th><th></th></tr></thead>
      <tbody>{list.map((u) => <tr key={u.id}><td><Av src={u.avatar} name={u.name} size={30} /></td><td>{u.name}</td><td>{u.address}</td><td>{u.email}</td><td>{who(u)}</td>
        <td><span className={"tag" + (u.active && u.approved ? "" : " off")}>{!u.approved ? "En attente" : u.active ? "Actif" : "Désactivé"}</span></td>
        <td style={{ whiteSpace: "nowrap" }}><button onClick={() => setEdit(u)}>Modifier</button>{" "}<button onClick={() => toggle(u)}>{u.active ? "Désactiver" : "Activer"}</button>{" "}<button className="danger" onClick={() => remove(u)}>Supprimer</button></td></tr>)}</tbody></table></div></div>);
}

function Pending({ refresh }) {
  const [list, setList] = useState([]);
  const load = () => api("admin/pending/").then((r) => r.ok && setList(r.data));
  useEffect(() => { load(); }, []);
  const act = async (a, id) => { await api("admin/" + a + "/" + id + "/", "POST"); load(); refresh(); };
  return (<div>{list.length === 0 && <p className="dim">Aucune demande en attente.</p>}
    {list.map((u) => <div key={u.id} className="item panel"><b>{u.name}</b> — {u.address} <small>({u.email}) · {u.joined}</small>
      <div style={{ marginTop: 8 }}><button className="pri" onClick={() => act("approve", u.id)}>Valider</button>{" "}<button className="danger" onClick={() => act("reject", u.id)}>Refuser</button></div></div>)}</div>);
}

function Admin({ refresh }) {
  const [tab, setTab] = useState("pending");
  return (<div><div className="tabs" style={{ maxWidth: 440 }}><button className={tab === "pending" ? "on" : ""} onClick={() => setTab("pending")}>Validations professeurs</button>
    <button className={tab === "users" ? "on" : ""} onClick={() => setTab("users")}>Utilisateurs</button></div>
    {tab === "pending" ? <Pending refresh={refresh} /> : <Users />}</div>);
}

function Profile({ me, setMe }) {
  const [f, setF] = useState({ name: me.name, username: me.username, phone: me.phone || "", level: me.level || "L1", parcours: me.parcours || "IG", notify: me.notify });
  const [pw, setPw] = useState({ old: "", new: "" }), [msg, setMsg] = useState(""), [msg2, setMsg2] = useState("");
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const save = async () => { const r = await api("me/", "PATCH", f); if (r.ok) { setMe(r.data); setMsg("✔ Enregistré"); } else setMsg("✖ " + err(r.data)); };
  const photo = async (e) => { const file = e.target.files[0]; if (!file) return; const fd = new FormData(); fd.append("file", file); const r = await api("me/avatar/", "POST", fd); r.ok ? setMe(r.data) : setMsg("✖ " + err(r.data)); e.target.value = ""; };
  const rmPhoto = async () => { const r = await api("me/avatar/", "DELETE"); if (r.ok) setMe(r.data); };
  const chPw = async () => { const r = await api("me/password/", "POST", pw); if (r.ok) { setMsg2("✔ Mot de passe modifié"); setPw({ old: "", new: "" }); } else setMsg2("✖ " + err(r.data)); };
  return (<div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
    <div className="panel pad" style={{ flex: "1 1 300px", maxWidth: 500 }}><h3>Mon profil</h3>
      <div className="from"><Av src={me.avatar} name={me.name} size={76} /><div>
        <label className="filebtn"><span className="att">📷 Changer la photo</span><input type="file" accept="image/*" onChange={photo} /></label>{" "}
        {me.avatar && <button className="link" onClick={rmPhoto}>Supprimer la photo</button>}<br /><small>{who(me)}</small></div></div>
      <p>Adresse ENI Mail : <span className="addr" style={{ fontSize: 15 }}>{me.address}</span></p>
      <small>Elle suit votre nom d'utilisateur. Les alertes sont envoyées à {me.email}.</small>
      <input placeholder="Nom complet" value={f.name} onChange={set("name")} /><input placeholder="Nom d'utilisateur" value={f.username} onChange={set("username")} autoCapitalize="none" />
      <input placeholder="Téléphone (facultatif)" value={f.phone} onChange={set("phone")} />
      {me.role === "student" && <div className="row"><select value={f.level} onChange={set("level")}>{LEVELS.map((l) => <option key={l}>{l}</option>)}</select>
        <select value={f.parcours} onChange={set("parcours")}>{PARCOURS.map((p) => <option key={p}>{p}</option>)}</select></div>}
      <label><input type="checkbox" checked={f.notify} onChange={(e) => setF({ ...f, notify: e.target.checked })} />Recevoir une alerte sur mon e-mail personnel</label>
      <p><button className="pri" onClick={save}>Enregistrer</button> <span className="msg">{msg}</span></p></div>
    <div className="panel pad" style={{ flex: "1 1 280px", maxWidth: 380, alignSelf: "flex-start" }}><h3>Mot de passe</h3>
      <input type="password" placeholder="Ancien mot de passe" value={pw.old} onChange={(e) => setPw({ ...pw, old: e.target.value })} />
      <input type="password" placeholder="Nouveau mot de passe (6 caractères min.)" value={pw.new} onChange={(e) => setPw({ ...pw, new: e.target.value })} />
      <p><button className="pri" onClick={chPw}>Modifier</button> <span className="msg">{msg2}</span></p></div></div>);
}

export default function App() {
  const [me, setMe] = useState(null), [view, setView] = useState("inbox"), [q, setQ] = useState(""), [stats, setStats] = useState({}), [tick, setTick] = useState(0);
  const [collapsed, setCollapsed] = useState(isMobile()), [menu, setMenu] = useState(false), [cw, setCw] = useState(null), [toast, setToast] = useState(""), [fs, setFs] = useState(false);
  const prev = useRef(null);
  const flash = (m) => { setToast(m); setTimeout(() => setToast(""), 4000); };
  useEffect(() => { const h = () => setFs(!!document.fullscreenElement); document.addEventListener("fullscreenchange", h); return () => document.removeEventListener("fullscreenchange", h); }, []);
  const toggleFs = () => (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen());
  const refresh = useCallback(() => api("stats/").then((r) => r.ok && setStats(r.data)), []);
  useEffect(() => { if (localStorage.getItem("token")) api("me/").then((r) => r.ok && setMe(r.data)); }, []);
  useEffect(() => { if (me) { refresh(); const t = setInterval(refresh, 12000); return () => clearInterval(t); } }, [me, refresh]);
  useEffect(() => {
    if (stats.unread == null) return;
    if (prev.current !== null && stats.unread > prev.current) { flash("📬 Nouveau message reçu"); setTick((t) => t + 1); }
    prev.current = stats.unread; document.title = (stats.unread > 0 ? "(" + stats.unread + ") " : "") + "ENI Mail";
  }, [stats.unread]);
  if (!me) return <Auth onLogin={setMe} />;
  const openCompose = (d) => setCw((c) => (c && !d ? { ...c, min: false } : { draft: d || null, key: Date.now(), min: false, max: false, full: false }));
  const nav = {
    reply: (m) => openCompose({ to: [{ id: m.from_id, name: m.from, address: m.from_address }], subject: /^re:/i.test(m.subject) ? m.subject : "Re: " + m.subject, body: "\n\n" + m.from + " a écrit :\n" + m.body.split("\n").map((l) => "> " + l).join("\n") }),
    forward: (m) => openCompose({ subject: /^(fwd|tr):/i.test(m.subject) ? m.subject : "Fwd: " + m.subject, body: "\n\n---------- Message transféré ----------\nDe : " + m.from + "\nObjet : " + m.subject + "\n\n" + m.body, keep: m.attachments }),
    draft: (m) => openCompose({ draft_id: m.mid, subject: m.subject, body: m.body, keep: m.attachments, ...m.draft }),
  };
  const go = (v) => { setQ(""); setView(v); if (isMobile()) setCollapsed(true); };
  const item = (v, ic, label, badge) => <button className={"nav" + (view === v ? " on" : "")} title={label} onClick={() => go(v)}>
    <span className="ic">{ic}</span><span className="lb">{label}</span>{badge > 0 && <span className="badge">{badge}</span>}</button>;
  const search = (v) => { setQ(v); if (!TITLES[view]) setView("inbox"); };
  return (<div onClick={() => menu && setMenu(false)}>
    <div className="topbar"><button className="iconbtn" title="Masquer / afficher le menu" onClick={() => setCollapsed((c) => !c)}>☰</button>
      <div className="brand"><img src="/logo.png" alt="ENI" /><b>ENI MAIL</b></div>
      <div className="search"><span>🔍</span><input placeholder="Rechercher dans les messages" value={q} onChange={(e) => search(e.target.value)} /></div>
      <button className="iconbtn fsbtn" title={fs ? "Quitter le plein écran" : "Plein écran"} onClick={toggleFs}>{fs ? "🗗" : "⛶"}</button>
      <div style={{ position: "relative" }} onClick={(e) => e.stopPropagation()}><button className="iconbtn" onClick={() => setMenu(!menu)}><Av src={me.avatar} name={me.name} size={38} /></button>
        {menu && <div className="menu glass"><div className="from"><Av src={me.avatar} name={me.name} size={52} /><div><b>{me.name}</b><br /><small>{who(me)}</small></div></div>
          <span className="addr" style={{ fontSize: 14 }}>{me.address}</span>
          <p style={{ display: "flex", gap: 8 }}><button onClick={() => { go("profile"); setMenu(false); }}>Mon profil</button>
            <button className="danger" onClick={() => { localStorage.removeItem("token"); setMe(null); }}>Déconnexion</button></p></div>}</div></div>
    <div className={"scrim" + (!collapsed ? " show" : "")} onClick={() => setCollapsed(true)} />
    <div className={"side" + (collapsed ? " collapsed" : "")}>
      <button className="cbtn pri" onClick={() => { openCompose(); if (isMobile()) setCollapsed(true); }} title="Nouveau message"><span>✎</span><span className="lb">Nouveau message</span></button>
      {item("inbox", "▣", "Réception", stats.unread)}{item("starred", "★", "Favoris")}{item("sent", "➤", "Envoyés")}{item("drafts", "✐", "Brouillons", stats.drafts)}
      {item("archive", "🗄", "Archives")}{item("trash", "🗑", "Corbeille")}{item("dir", "👥", "Annuaire")}{item("home", "⌂", "Tableau de bord")}
      {me.role === "admin" && item("admin", "⚙", "Administration", stats.pending)}{item("profile", "☰", "Mon profil")}</div>
    <div className={"main" + (collapsed ? " collapsed" : "")}><div className="view" key={view}>
      {view === "home" && <Home me={me} stats={stats} flash={flash} openCompose={openCompose} go={go} />}
      {view === "dir" && <Directory onWrite={(u) => openCompose({ to: [{ id: u.id, name: u.name, address: u.address }] })} />}
      {TITLES[view] && <List kind={view} q={q} nav={nav} refresh={refresh} tick={tick} />}
      {view === "admin" && <Admin refresh={refresh} />}
      {view === "profile" && <Profile me={me} setMe={setMe} />}</div></div>
    {!cw && <button className="fab pri" title="Nouveau message" onClick={() => openCompose()}>✎</button>}
    {cw && cw.max && <div className="cw-back" onClick={() => setCw({ ...cw, max: false })} />}
    {cw && <Compose key={cw.key} me={me} cw={cw} setCw={setCw} close={() => setCw(null)} refresh={refresh} flash={flash}
      onSent={(n) => { setCw(null); refresh(); setTick((t) => t + 1); flash("Message envoyé à " + n + " personne(s)"); }} />}
    {toast && <div className="toast" key={toast}>{toast}</div>}
  </div>);
}
