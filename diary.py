"""
diary.py — Farm Diary Module v3 (BUG FIXED)
Fix: View Full Chat now works — replaced JSON.stringify in onclick with ID-based lookup.
New: Nearby Agri Shop locator page at /agri-shops.

Add to main.py:
    from diary import diary_router
    app.include_router(diary_router)
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, HTMLResponse
from pymongo import MongoClient
from bson import ObjectId
import os, logging
from datetime import datetime

logger = logging.getLogger(__name__)
diary_router = APIRouter()

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
_client   = MongoClient(MONGO_URI)
_db       = _client.get_database("plant_disease_db")
diary_col = _db.get_collection("diary")


# ─────────────────────────────────────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@diary_router.post("/diary/save")
async def save_diary_entry(request: Request):
    try:
        body       = await request.json()
        doc = {
            "type":      body.get("type", "chat"),
            "title":     body.get("title", "Untitled Entry"),
            "content":   body.get("content", {}),
            "tags":      body.get("tags", []),
            "crop":      body.get("crop", ""),
            "language":  body.get("language", "english"),
            "timestamp": int(datetime.now().timestamp()),
            "date_str":  datetime.now().strftime("%d %B %Y, %I:%M %p"),
        }
        result = diary_col.insert_one(doc)
        return JSONResponse({"status": "success", "id": str(result.inserted_id)})
    except Exception as e:
        logger.error(f"Diary save error: {e}")
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)


@diary_router.get("/diary/entries")
async def get_diary_entries(limit: int = 100, entry_type: str = ""):
    try:
        query = {}
        if entry_type in ("chat", "detection"):
            query["type"] = entry_type
        docs = list(diary_col.find(query).sort("timestamp", -1).limit(limit))
        for d in docs:
            d["_id"] = str(d["_id"])
        return JSONResponse({"status": "success", "entries": docs})
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)


@diary_router.delete("/diary/entries/{entry_id}")
async def delete_diary_entry(entry_id: str):
    try:
        if not ObjectId.is_valid(entry_id):
            return JSONResponse({"status": "error", "detail": "Invalid ID"}, status_code=400)
        result = diary_col.delete_one({"_id": ObjectId(entry_id)})
        if result.deleted_count:
            return JSONResponse({"status": "success"})
        return JSONResponse({"status": "error", "detail": "Entry not found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)


@diary_router.get("/diary/stats")
async def get_diary_stats():
    try:
        total      = diary_col.count_documents({})
        chats      = diary_col.count_documents({"type": "chat"})
        detections = diary_col.count_documents({"type": "detection"})
        pipeline   = [
            {"$match": {"type": "detection"}},
            {"$group": {"_id": "$content.disease_name", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 1}
        ]
        top         = list(diary_col.aggregate(pipeline))
        top_disease = top[0]["_id"] if top else "—"
        return JSONResponse({
            "status": "success",
            "total": total, "chats": chats,
            "detections": detections, "top_disease": top_disease
        })
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)


@diary_router.get("/diary")
async def diary_page():
    return HTMLResponse(content=_diary_html())


@diary_router.get("/agri-shops")
async def agri_shops_page():
    return HTMLResponse(content=_shops_html())


# ─────────────────────────────────────────────────────────────────────────────
# DIARY HTML
# ─────────────────────────────────────────────────────────────────────────────

def _diary_html() -> str:
    return r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>My Farm Diary – PlantDoc AI</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,500&family=Crimson+Pro:wght@300;400;500;600&display=swap" rel="stylesheet"/>
<style>
:root{
  --ink:#1a1208;--bark:#4a2c0a;--rust:#8b4513;--amber:#c8752a;
  --wheat:#f5deb3;--parch:#fdf6e3;--sage:#5a7a3a;--moss:#3d5a27;
  --sky:#e8f4ea;--fog:#e6d8c0;--line:#d4c4a0;--white:#fffef9;
  --user-bg:#2d5a27;--bot-bg:#f0f7ec;
}
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Crimson Pro',serif;background:var(--parch);color:var(--ink);min-height:100vh;
  background-image:repeating-linear-gradient(0deg,transparent,transparent 27px,rgba(180,160,120,.1) 27px,rgba(180,160,120,.1) 28px);}

.navbar{background:var(--bark);padding:.9rem 2rem;box-shadow:0 3px 15px rgba(0,0,0,.3);}
.nav-container{max-width:1200px;margin:0 auto;display:flex;justify-content:space-between;align-items:center;}
.logo{font-family:'Playfair Display',serif;font-size:1.4rem;color:var(--wheat);font-weight:700;}
.nav-links{display:flex;list-style:none;gap:1.2rem;flex-wrap:wrap;}
.nav-links a{text-decoration:none;color:rgba(245,222,179,.75);font-size:.88rem;font-weight:500;padding:.3rem .65rem;border-radius:4px;transition:all .2s;}
.nav-links a:hover,.nav-links a.active{color:var(--wheat);background:rgba(255,255,255,.12);}

.page-header{background:linear-gradient(135deg,var(--bark) 0%,var(--rust) 60%,var(--amber) 100%);
  padding:2.5rem 2rem 2rem;text-align:center;position:relative;overflow:hidden;}
.page-header::before{content:'📔';font-size:8rem;position:absolute;right:-1rem;top:-1rem;opacity:.08;}
.page-header h1{font-family:'Playfair Display',serif;font-size:2.2rem;color:var(--wheat);margin-bottom:.3rem;}
.page-header p{color:rgba(245,222,179,.85);font-size:1rem;}

.stats-bar{background:var(--bark);padding:.9rem 2rem;}
.stats-inner{max-width:1200px;margin:0 auto;display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;}
.stat-box{text-align:center;padding:.5rem;}
.stat-num{font-family:'Playfair Display',serif;font-size:1.7rem;color:var(--wheat);font-weight:700;}
.stat-label{font-size:.72rem;color:rgba(245,222,179,.6);text-transform:uppercase;letter-spacing:.05em;}

.main{max-width:1200px;margin:2rem auto;padding:0 1.5rem;display:grid;grid-template-columns:210px 1fr;gap:2rem;}
@media(max-width:720px){.main{grid-template-columns:1fr;}}

.filter-panel{display:flex;flex-direction:column;gap:1rem;}
.filter-card{background:var(--white);border-radius:10px;box-shadow:0 2px 12px rgba(74,44,10,.1);overflow:hidden;border:1px solid var(--line);}
.filter-header{background:var(--fog);padding:.7rem 1rem;font-family:'Playfair Display',serif;font-size:.92rem;color:var(--bark);border-bottom:1px solid var(--line);}
.filter-body{padding:.9rem;}
.filter-btn{display:block;width:100%;text-align:left;background:none;border:1px solid transparent;padding:.5rem .75rem;border-radius:6px;font-family:'Crimson Pro',serif;font-size:.93rem;color:var(--bark);cursor:pointer;margin-bottom:.3rem;transition:all .2s;}
.filter-btn:hover{background:var(--sky);border-color:var(--sage);}
.filter-btn.active{background:var(--sage);color:white;border-color:var(--moss);}
.filter-btn:last-child{margin-bottom:0;}

.timeline{position:relative;}
.timeline::before{content:'';position:absolute;left:20px;top:0;bottom:0;width:2px;
  background:linear-gradient(to bottom,var(--amber),var(--sage));border-radius:2px;}
.t-entry{display:flex;gap:1.2rem;margin-bottom:1.5rem;animation:fadeSlide .35s ease both;}
@keyframes fadeSlide{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}
.t-dot{width:42px;height:42px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:1.3rem;border:3px solid var(--white);box-shadow:0 2px 8px rgba(0,0,0,.15);z-index:1;}
.t-dot.chat{background:linear-gradient(135deg,var(--sage),var(--moss));}
.t-dot.detection{background:linear-gradient(135deg,var(--amber),var(--rust));}

.t-card{flex:1;background:var(--white);border-radius:12px;padding:1.1rem 1.3rem;box-shadow:0 3px 15px rgba(74,44,10,.07);border:1px solid var(--line);transition:box-shadow .2s;}
.t-card:hover{box-shadow:0 5px 20px rgba(74,44,10,.12);}
.t-card-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:.75rem;}
.t-title{font-family:'Playfair Display',serif;font-size:1rem;color:var(--bark);font-weight:700;}
.t-date{font-size:.73rem;color:#8a7a5a;white-space:nowrap;margin-left:.5rem;}
.t-type-badge{font-size:.68rem;padding:.17rem .52rem;border-radius:10px;font-weight:600;text-transform:uppercase;letter-spacing:.04em;}
.t-type-badge.chat{background:#e8f5e3;color:var(--moss);}
.t-type-badge.detection{background:#fef3e2;color:var(--rust);}

.chat-preview{margin-top:.6rem;border-top:1px solid var(--line);padding-top:.65rem;}
.preview-msg{display:flex;gap:.5rem;margin-bottom:.4rem;font-size:.87rem;line-height:1.4;}
.pm-role{font-weight:700;flex-shrink:0;font-size:.76rem;padding-top:.05rem;}
.pm-role.user{color:var(--rust);}
.pm-role.assistant{color:var(--sage);}
.pm-text{color:#4a3a2a;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;}

.disease-pill{display:inline-block;background:var(--fog);border-radius:8px;padding:.18rem .65rem;font-weight:600;color:var(--bark);margin:.2rem .2rem 0 0;font-size:.88rem;}
.severity-high{color:#c53030;font-weight:600;}
.severity-medium{color:var(--rust);font-weight:600;}
.severity-none{color:var(--moss);font-weight:600;}

.t-tags{display:flex;flex-wrap:wrap;gap:.3rem;margin-top:.65rem;}
.t-tag{font-size:.68rem;padding:.12rem .48rem;border-radius:7px;background:var(--fog);color:var(--bark);border:1px solid var(--line);}

.t-footer{display:flex;justify-content:space-between;align-items:center;margin-top:.8rem;padding-top:.7rem;border-top:1px solid var(--line);}
.msg-count{font-size:.76rem;color:#9a8a6a;font-style:italic;}
.footer-btns{display:flex;gap:.5rem;}
.view-btn{background:var(--sage);border:none;color:white;border-radius:6px;padding:.3rem .85rem;font-size:.8rem;cursor:pointer;font-family:'Crimson Pro',serif;font-weight:600;transition:all .2s;}
.view-btn:hover{background:var(--moss);transform:translateY(-1px);}
.del-btn{background:none;border:1px solid #e0c8b0;color:#b08060;border-radius:6px;padding:.3rem .7rem;font-size:.78rem;cursor:pointer;font-family:'Crimson Pro',serif;transition:all .2s;}
.del-btn:hover{background:#fff0ec;border-color:var(--rust);color:var(--rust);}

.empty-state{text-align:center;padding:4rem 2rem;color:#8a7a5a;}
.empty-state .empty-icon{font-size:4rem;margin-bottom:1rem;opacity:.5;}
.empty-state h3{font-family:'Playfair Display',serif;font-size:1.4rem;color:var(--bark);margin-bottom:.5rem;}
.loading{text-align:center;padding:3rem;color:var(--amber);font-style:italic;font-size:1.05rem;}

/* ── MODAL ─────────────────────────────────────────────────────────── */
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(26,18,8,.7);z-index:9999;
  align-items:center;justify-content:center;padding:1rem;backdrop-filter:blur(4px);}
.modal-overlay.open{display:flex;}
.modal{background:var(--white);border-radius:16px;width:100%;max-width:700px;max-height:90vh;
  display:flex;flex-direction:column;box-shadow:0 20px 60px rgba(0,0,0,.4);border:2px solid var(--line);
  animation:modalIn .22s ease;}
@keyframes modalIn{from{opacity:0;transform:scale(.94) translateY(10px)}to{opacity:1;transform:none}}

.modal-header{padding:1.1rem 1.4rem;background:linear-gradient(135deg,var(--bark),var(--rust));
  border-radius:14px 14px 0 0;display:flex;justify-content:space-between;align-items:center;flex-shrink:0;}
.modal-title{font-family:'Playfair Display',serif;color:var(--wheat);font-size:1.1rem;margin-bottom:.12rem;}
.modal-meta{font-size:.76rem;color:rgba(245,222,179,.7);}
.modal-close{background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);color:var(--wheat);
  border-radius:6px;padding:.35rem .8rem;font-size:.88rem;cursor:pointer;transition:all .2s;flex-shrink:0;}
.modal-close:hover{background:rgba(255,255,255,.28);}

.modal-chat{flex:1;overflow-y:auto;padding:1.2rem 1.3rem;display:flex;flex-direction:column;gap:1rem;
  min-height:0;}
.modal-chat::-webkit-scrollbar{width:5px;}
.modal-chat::-webkit-scrollbar-thumb{background:var(--fog);border-radius:4px;}

.chat-msg{display:flex;gap:.55rem;max-width:86%;}
.chat-msg.user{flex-direction:row-reverse;align-self:flex-end;}
.chat-msg.assistant{align-self:flex-start;}
.chat-msg-avatar{width:34px;height:34px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:1.1rem;}
.chat-msg.user      .chat-msg-avatar{background:var(--user-bg);}
.chat-msg.assistant .chat-msg-avatar{background:var(--bot-bg);border:1.5px solid var(--line);}
.chat-msg-bubble{padding:.7rem 1rem;border-radius:13px;font-size:.93rem;line-height:1.65;font-family:'Crimson Pro',serif;}
.chat-msg.user      .chat-msg-bubble{background:var(--user-bg);color:white;border-bottom-right-radius:3px;}
.chat-msg.assistant .chat-msg-bubble{background:var(--bot-bg);color:var(--ink);border-bottom-left-radius:3px;border:1px solid var(--line);}
.chat-msg-bubble ul{padding-left:1.1rem;margin:.3rem 0;}
.chat-msg-bubble li{margin-bottom:.2rem;}
.chat-msg-bubble strong{color:var(--moss);}
.chat-msg.user .chat-msg-bubble strong{color:#c8f0b8;}
.chat-msg-label{font-size:.68rem;opacity:.5;margin-top:.22rem;}
.chat-msg.user      .chat-msg-label{text-align:right;}
.chat-msg.assistant .chat-msg-label{text-align:left;}

.context-chip{background:#fff8ee;border:1.5px solid #e8d8a0;border-radius:8px;padding:.6rem 1rem;
  font-size:.83rem;color:var(--bark);margin-bottom:.3rem;font-style:italic;line-height:1.5;}

.modal-footer{padding:.85rem 1.4rem;border-top:1px solid var(--line);display:flex;justify-content:space-between;
  align-items:center;background:var(--fog);border-radius:0 0 14px 14px;flex-shrink:0;}
.modal-footer-info{font-size:.78rem;color:#8a7a6a;}
.modal-copy-btn{background:var(--sage);border:none;color:white;border-radius:7px;padding:.4rem 1rem;
  font-size:.82rem;cursor:pointer;font-family:'Crimson Pro',serif;font-weight:600;transition:all .2s;}
.modal-copy-btn:hover{background:var(--moss);}
</style>
</head>
<body>

<nav class="navbar">
  <div class="nav-container">
    <div class="logo">🌿 PlantDoc AI</div>
    <ul class="nav-links">
      <li><a href="/">Home</a></li>
      <li><a href="/predict">Predict</a></li>
      <li><a href="/consultation">Expert Help</a></li>
      <li><a href="/crop-calendar">Crop Calendar</a></li>
      <li><a href="/diary" class="active">My Diary</a></li>
      <li><a href="/agri-shops">🏪 Agri Shops</a></li>
      <li><a href="/records-page">Records</a></li>
    </ul>
  </div>
</nav>

<div class="page-header">
  <h1>📔 My Farm Diary</h1>
  <p>Your personal timeline of disease detections and expert consultations</p>
</div>

<div class="stats-bar">
  <div class="stats-inner">
    <div class="stat-box"><div class="stat-num" id="statTotal">—</div><div class="stat-label">Total Entries</div></div>
    <div class="stat-box"><div class="stat-num" id="statChats">—</div><div class="stat-label">Consultations</div></div>
    <div class="stat-box"><div class="stat-num" id="statDetections">—</div><div class="stat-label">Detections</div></div>
    <div class="stat-box"><div class="stat-num" id="statTopDisease" style="font-size:.92rem;padding-top:.55rem">—</div><div class="stat-label">Most Common Disease</div></div>
  </div>
</div>

<div class="main">
  <aside class="filter-panel">
    <div class="filter-card">
      <div class="filter-header">📂 Filter</div>
      <div class="filter-body">
        <button class="filter-btn active" onclick="setFilter('all',this)">📋 All Entries</button>
        <button class="filter-btn" onclick="setFilter('chat',this)">💬 Consultations</button>
        <button class="filter-btn" onclick="setFilter('detection',this)">🔬 Detections</button>
      </div>
    </div>
    <div class="filter-card">
      <div class="filter-header">ℹ️ How it works</div>
      <div class="filter-body" style="font-size:.85rem;color:#6a5a3a;line-height:1.65;">
        <strong>💬 Save chats</strong> — click "Save to Diary" in Expert Help<br><br>
        <strong>👁 View chat</strong> — click the <strong style="color:var(--sage)">View Full Chat</strong> button on any entry<br><br>
        <strong>🔬 Detections</strong> — auto-saved from the Predict page
      </div>
    </div>
    <div class="filter-card">
      <div class="filter-header">🏪 Nearby Shops</div>
      <div class="filter-body">
        <a href="/agri-shops" style="display:block;background:var(--sage);color:white;text-align:center;padding:.6rem;border-radius:7px;text-decoration:none;font-weight:600;font-size:.88rem;">
          Find Agri Shops Near Me →
        </a>
      </div>
    </div>
  </aside>

  <div>
    <div id="timelineContainer"><div class="loading">📖 Loading your farm diary…</div></div>
  </div>
</div>

<!-- MODAL -->
<div class="modal-overlay" id="chatModal">
  <div class="modal">
    <div class="modal-header">
      <div>
        <div class="modal-title" id="modalTitle">Farm Consultation</div>
        <div class="modal-meta"  id="modalMeta"></div>
      </div>
      <button class="modal-close" id="modalCloseBtn">✕ Close</button>
    </div>
    <div class="modal-chat" id="modalChat"></div>
    <div class="modal-footer">
      <span class="modal-footer-info" id="modalFooterInfo"></span>
      <button class="modal-copy-btn" id="modalCopyBtn">📋 Copy Chat</button>
    </div>
  </div>
</div>

<script>
// ── State ──────────────────────────────────────────────────────────────────
let allEntries     = [];
let entryMap       = {};          // key: _id  → entry object (THE FIX)
let currentFilter  = 'all';
let currentEntry   = null;

// ── Modal wiring (done ONCE at page load, not inside onclick attrs) ─────────
const modalOverlay = document.getElementById('chatModal');
const modalClose   = document.getElementById('modalCloseBtn');
const modalCopy    = document.getElementById('modalCopyBtn');

modalClose.addEventListener('click', closeModal);
modalCopy.addEventListener ('click', copyChat);
modalOverlay.addEventListener('click', e => { if (e.target === modalOverlay) closeModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

// ── Stats ──────────────────────────────────────────────────────────────────
async function loadStats() {
  try {
    const r = await fetch('/diary/stats');
    const d = await r.json();
    if (d.status === 'success') {
      document.getElementById('statTotal').textContent      = d.total;
      document.getElementById('statChats').textContent      = d.chats;
      document.getElementById('statDetections').textContent = d.detections;
      document.getElementById('statTopDisease').textContent = d.top_disease || '—';
    }
  } catch(e) {}
}

// ── Load entries ───────────────────────────────────────────────────────────
async function loadEntries() {
  try {
    const r = await fetch('/diary/entries?limit=100');
    const d = await r.json();
    if (d.status === 'success') {
      allEntries = d.entries;
      // Build the lookup map — THIS is how we avoid JSON.stringify in onclick
      entryMap = {};
      allEntries.forEach(e => { entryMap[e._id] = e; });
      renderTimeline();
    }
  } catch(e) {
    document.getElementById('timelineContainer').innerHTML =
      '<div class="empty-state"><div class="empty-icon">⚠️</div><h3>Could not load diary</h3><p>Check your connection and refresh.</p></div>';
  }
}

// ── Filter ─────────────────────────────────────────────────────────────────
function setFilter(type, btn) {
  currentFilter = type;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderTimeline();
}

// ── Timeline ───────────────────────────────────────────────────────────────
function renderTimeline() {
  const container = document.getElementById('timelineContainer');
  const filtered  = currentFilter === 'all'
    ? allEntries
    : allEntries.filter(e => e.type === currentFilter);

  if (!filtered.length) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📔</div>
        <h3>No entries yet</h3>
        <p>Save a chat from Expert Help or run a detection to start your diary.</p>
        <br><a href="/consultation" style="color:var(--sage);font-weight:600;">Go to Expert Help →</a>
      </div>`;
    return;
  }
  container.innerHTML = `<div class="timeline">${filtered.map(buildCard).join('')}</div>`;
}

// ── Build card (NO JSON.stringify in onclick) ──────────────────────────────
function buildCard(e) {
  const isDetection = e.type === 'detection';
  const c    = e.content  || {};
  const msgs = c.messages || [];
  let bodyHtml = '';

  if (isDetection) {
    const sev      = (c.severity || '').toLowerCase();
    const sevClass = sev === 'high' ? 'severity-high' : sev === 'medium' ? 'severity-medium' : 'severity-none';
    bodyHtml = `
      <span class="disease-pill">${esc(c.disease_name || 'Unknown')}</span>
      <span class="disease-pill">Confidence: ${c.confidence ? (c.confidence*100).toFixed(1)+'%' : '—'}</span><br>
      <span style="font-size:.87rem;margin-top:.3rem;display:inline-block;">
        Severity: <span class="${sevClass}">${esc(c.severity || '—')}</span>
      </span>
      ${c.treatment ? `<div style="margin-top:.5rem;font-size:.86rem;color:#5a4a2a;line-height:1.5;">💊 ${esc(c.treatment).substring(0,120)}…</div>` : ''}`;
  } else {
    if (msgs.length) {
      const preview = msgs.slice(0, 3);
      bodyHtml = `<div class="chat-preview">
        ${preview.map(m => `
          <div class="preview-msg">
            <span class="pm-role ${m.role}">${m.role === 'user' ? '👨‍🌾 You' : '🌱 AgriDoc'}</span>
            <span class="pm-text">${esc(m.content || '').substring(0, 110)}${(m.content||'').length > 110 ? '…' : ''}</span>
          </div>`).join('')}
        ${msgs.length > 3 ? `<div style="font-size:.76rem;color:#9a8a6a;margin-top:.35rem;font-style:italic;">+ ${msgs.length - 3} more messages — click View Full Chat</div>` : ''}
      </div>`;
    } else {
      bodyHtml = `<span style="color:#9a8a6a;font-style:italic;font-size:.88rem;">No messages saved.</span>`;
    }
  }

  const tags     = (e.tags || []).map(t => `<span class="t-tag">${esc(t)}</span>`).join('');
  const msgCount = msgs.length ? `${msgs.length} message${msgs.length !== 1 ? 's' : ''}` : '';
  const showView = !isDetection && msgs.length > 0;

  // ✅ FIX: pass only the entry _id — look up full object from entryMap in JS
  return `
    <div class="t-entry" id="entry-${e._id}">
      <div class="t-dot ${e.type}">${isDetection ? '🔬' : '💬'}</div>
      <div class="t-card">
        <div class="t-card-header">
          <div>
            <div class="t-title">${esc(e.title || 'Untitled')}</div>
            ${e.crop ? `<div style="font-size:.76rem;color:var(--sage);margin-top:.1rem;">🌾 ${esc(e.crop)}</div>` : ''}
          </div>
          <div style="display:flex;flex-direction:column;align-items:flex-end;gap:.22rem;">
            <span class="t-type-badge ${e.type}">${e.type}</span>
            <span class="t-date">${e.date_str || ''}</span>
          </div>
        </div>
        <div>${bodyHtml}</div>
        ${tags ? `<div class="t-tags">${tags}</div>` : ''}
        <div class="t-footer">
          <span class="msg-count">${msgCount}</span>
          <div class="footer-btns">
            ${showView ? `<button class="view-btn" onclick="openModalById('${e._id}')">👁 View Full Chat</button>` : ''}
            <button class="del-btn" onclick="deleteEntry('${e._id}')">🗑 Delete</button>
          </div>
        </div>
      </div>
    </div>`;
}

// ── Helpers ────────────────────────────────────────────────────────────────
function esc(t) {
  return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function fmtBubble(text) {
  return esc(text)
    .replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>')
    .replace(/\*(.*?)\*/g,'<em>$1</em>')
    .replace(/^[-*•]\s(.+)$/gm,'<li>$1</li>')
    .replace(/(<li>.*?<\/li>\n?)+/gs, m => `<ul>${m}</ul>`)
    .replace(/\n/g,'<br>');
}

// ── Open modal — looks up entry safely from entryMap ──────────────────────
function openModalById(id) {
  const entry = entryMap[id];
  if (!entry) { console.error('Entry not found:', id); return; }
  openModal(entry);
}

function openModal(entry) {
  currentEntry = entry;
  const c    = entry.content || {};
  const msgs = c.messages   || [];

  document.getElementById('modalTitle').textContent =
    entry.title || 'Farm Consultation';
  document.getElementById('modalMeta').textContent  =
    `${entry.date_str || ''} · ${msgs.length} message${msgs.length !== 1 ? 's' : ''} · Language: ${entry.language || 'English'}`;

  const chatDiv = document.getElementById('modalChat');
  chatDiv.innerHTML = '';

  // Show scan context chip if present
  if (c.context_used) {
    const chip = document.createElement('div');
    chip.className   = 'context-chip';
    chip.textContent = '📋 Scan context used: ' + c.context_used;
    chatDiv.appendChild(chip);
  }

  if (!msgs.length) {
    chatDiv.innerHTML = '<div style="text-align:center;padding:2rem;color:#9a8a6a;font-style:italic;">No messages were saved in this entry.</div>';
  }

  // Render every message as a full bubble
  msgs.forEach(m => {
    const wrap = document.createElement('div');
    wrap.className = 'chat-msg ' + (m.role || 'user');

    const avatar = document.createElement('div');
    avatar.className   = 'chat-msg-avatar';
    avatar.textContent = m.role === 'user' ? '👨‍🌾' : '🌱';

    const body = document.createElement('div');
    body.innerHTML = `
      <div class="chat-msg-bubble">${fmtBubble(m.content || '(empty)')}</div>
      <div class="chat-msg-label">${m.role === 'user' ? 'You' : 'AgriDoc'}</div>`;

    wrap.appendChild(avatar);
    wrap.appendChild(body);
    chatDiv.appendChild(wrap);
  });

  document.getElementById('modalFooterInfo').textContent =
    `Saved on ${entry.date_str || 'unknown date'}`;

  modalOverlay.classList.add('open');
  // Scroll chat to top after render
  requestAnimationFrame(() => { chatDiv.scrollTop = 0; });
}

function closeModal() {
  modalOverlay.classList.remove('open');
  currentEntry = null;
}

// ── Copy chat ──────────────────────────────────────────────────────────────
function copyChat() {
  if (!currentEntry) return;
  const msgs = (currentEntry.content || {}).messages || [];
  const text = [
    `=== ${currentEntry.title || 'Farm Consultation'} ===`,
    `Date: ${currentEntry.date_str || ''}`,
    '',
    ...msgs.map(m =>
      `${m.role === 'user' ? '👨‍🌾 You' : '🌱 AgriDoc'}:\n${m.content || ''}`
    )
  ].join('\n\n');

  navigator.clipboard.writeText(text).then(() => {
    modalCopy.textContent = '✅ Copied!';
    setTimeout(() => { modalCopy.textContent = '📋 Copy Chat'; }, 2500);
  }).catch(() => { alert('Could not copy. Try selecting the text manually.'); });
}

// ── Delete entry ───────────────────────────────────────────────────────────
async function deleteEntry(id) {
  if (!confirm('Delete this diary entry permanently?')) return;
  try {
    const r = await fetch(`/diary/entries/${id}`, { method: 'DELETE' });
    const d = await r.json();
    if (d.status === 'success') {
      allEntries = allEntries.filter(e => e._id !== id);
      delete entryMap[id];
      renderTimeline();
      loadStats();
    }
  } catch(e) { alert('Could not delete entry.'); }
}

// ── Init ───────────────────────────────────────────────────────────────────
loadStats();
loadEntries();
</script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# AGRI SHOPS HTML  (Leaflet.js + OpenStreetMap — 100% free, no API key)
# ─────────────────────────────────────────────────────────────────────────────

def _shops_html() -> str:
    return r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Nearby Agri Shops – PlantDoc AI</title>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&family=Merriweather:wght@400;700&display=swap" rel="stylesheet"/>
<!-- Leaflet CSS -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"/>
<!-- Leaflet JS -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<style>
:root{
  --green-dark:#1b4332;--green-mid:#2d6a4f;--green-light:#52b788;
  --green-pale:#d8f3dc;--earth:#5c4033;--cream:#f9f4ef;--white:#ffffff;
  --warn:#f4a261;--danger:#e63946;--border:#c8dfc8;--text:#1a2e1a;--muted:#5a7a5a;
}
*{margin:0;padding:0;box-sizing:border-box;}
html,body{height:100%;font-family:'Nunito',sans-serif;background:var(--cream);color:var(--text);}

/* ── Navbar ── */
.navbar{background:var(--green-dark);padding:.85rem 2rem;box-shadow:0 3px 12px rgba(0,0,0,.25);position:relative;z-index:1000;}
.nav-container{max-width:1300px;margin:0 auto;display:flex;justify-content:space-between;align-items:center;}
.logo{font-family:'Merriweather',serif;font-size:1.3rem;color:#a8d5a2;font-weight:700;}
.nav-links{display:flex;list-style:none;gap:1.2rem;flex-wrap:wrap;}
.nav-links a{text-decoration:none;color:rgba(168,213,162,.78);font-size:.88rem;font-weight:600;padding:.3rem .65rem;border-radius:5px;transition:all .2s;}
.nav-links a:hover,.nav-links a.active{color:#a8d5a2;background:rgba(255,255,255,.1);}

/* ── Hero ── */
.hero{background:linear-gradient(135deg,var(--green-dark) 0%,var(--green-mid) 100%);
  padding:2rem 2rem 1.5rem;text-align:center;}
.hero h1{font-family:'Merriweather',serif;font-size:1.9rem;color:white;margin-bottom:.3rem;}
.hero p{color:rgba(255,255,255,.82);font-size:.98rem;}

/* ── Page layout ── */
.page-body{display:grid;grid-template-columns:360px 1fr;height:calc(100vh - 145px);max-width:1400px;margin:0 auto;}
@media(max-width:800px){.page-body{grid-template-columns:1fr;height:auto;}}

/* ── Sidebar ── */
.sidebar{display:flex;flex-direction:column;background:white;border-right:1px solid var(--border);overflow:hidden;}

.search-area{padding:1rem;border-bottom:1px solid var(--border);background:var(--green-pale);}
.search-area h3{font-size:.95rem;color:var(--green-dark);font-weight:800;margin-bottom:.7rem;}

.locate-btn{width:100%;padding:.75rem;background:var(--green-mid);color:white;border:none;
  border-radius:9px;font-family:'Nunito',sans-serif;font-weight:800;font-size:.95rem;
  cursor:pointer;transition:all .25s;display:flex;align-items:center;justify-content:center;gap:.5rem;}
.locate-btn:hover{background:var(--green-dark);transform:translateY(-1px);}
.locate-btn:disabled{opacity:.55;cursor:not-allowed;transform:none;}

.radius-row{display:flex;align-items:center;gap:.6rem;margin-top:.7rem;}
.radius-label{font-size:.82rem;color:var(--muted);white-space:nowrap;font-weight:600;}
.radius-select{flex:1;padding:.45rem .7rem;border:1.5px solid var(--border);border-radius:7px;
  font-family:'Nunito',sans-serif;font-size:.85rem;color:var(--text);background:white;cursor:pointer;}
.radius-select:focus{outline:none;border-color:var(--green-light);}

.type-chips{display:flex;flex-wrap:wrap;gap:.4rem;margin-top:.7rem;}
.type-chip{padding:.3rem .75rem;border-radius:20px;border:1.5px solid var(--border);
  background:white;font-size:.78rem;font-weight:700;cursor:pointer;transition:all .2s;color:var(--muted);}
.type-chip.active{background:var(--green-mid);color:white;border-color:var(--green-mid);}

.status-bar{padding:.6rem 1rem;font-size:.82rem;color:var(--muted);background:#f5faf5;
  border-bottom:1px solid var(--border);min-height:36px;display:flex;align-items:center;gap:.4rem;}
.status-dot{width:8px;height:8px;border-radius:50%;background:var(--border);flex-shrink:0;}
.status-dot.green{background:var(--green-light);}
.status-dot.orange{background:var(--warn);}
.status-dot.pulse{animation:dotPulse 1.2s infinite;}
@keyframes dotPulse{0%,100%{opacity:1}50%{opacity:.3}}

/* ── Shop list ── */
.shop-list{flex:1;overflow-y:auto;padding:.5rem;}
.shop-list::-webkit-scrollbar{width:5px;}
.shop-list::-webkit-scrollbar-thumb{background:var(--border);border-radius:4px;}

.shop-card{background:white;border:1.5px solid var(--border);border-radius:11px;padding:.9rem 1rem;
  margin-bottom:.6rem;cursor:pointer;transition:all .22s;position:relative;}
.shop-card:hover{border-color:var(--green-light);box-shadow:0 4px 14px rgba(45,106,79,.12);transform:translateY(-1px);}
.shop-card.active{border-color:var(--green-mid);box-shadow:0 4px 16px rgba(45,106,79,.2);background:var(--green-pale);}

.shop-num{position:absolute;top:.65rem;right:.7rem;width:22px;height:22px;border-radius:50%;
  background:var(--green-mid);color:white;font-size:.7rem;font-weight:800;
  display:flex;align-items:center;justify-content:center;}
.shop-name{font-weight:800;font-size:.95rem;color:var(--green-dark);margin-bottom:.2rem;padding-right:1.8rem;}
.shop-type{font-size:.75rem;color:var(--muted);margin-bottom:.4rem;font-weight:600;text-transform:uppercase;letter-spacing:.04em;}
.shop-dist{font-size:.8rem;font-weight:700;color:var(--green-mid);}
.shop-addr{font-size:.78rem;color:#7a9a7a;margin-top:.2rem;line-height:1.4;}
.shop-tags{display:flex;flex-wrap:wrap;gap:.3rem;margin-top:.45rem;}
.shop-tag{font-size:.68rem;padding:.12rem .45rem;border-radius:6px;background:var(--green-pale);
  color:var(--green-dark);font-weight:700;}

.shop-actions{display:flex;gap:.45rem;margin-top:.6rem;}
.shop-btn{flex:1;padding:.38rem;border-radius:7px;border:1.5px solid var(--border);background:white;
  font-family:'Nunito',sans-serif;font-size:.76rem;font-weight:700;cursor:pointer;
  transition:all .2s;color:var(--text);text-align:center;text-decoration:none;display:block;}
.shop-btn:hover{background:var(--green-pale);border-color:var(--green-light);}
.shop-btn.primary{background:var(--green-mid);color:white;border-color:var(--green-mid);}
.shop-btn.primary:hover{background:var(--green-dark);}

.no-shops{text-align:center;padding:2.5rem 1rem;color:var(--muted);}
.no-shops .ns-icon{font-size:2.5rem;margin-bottom:.6rem;opacity:.5;}

/* ── Map ── */
#map{width:100%;height:100%;min-height:500px;}
@media(max-width:800px){#map{height:400px;}}

/* Loading spinner */
.spinner{display:inline-block;width:14px;height:14px;border:2px solid rgba(255,255,255,.4);
  border-top-color:white;border-radius:50%;animation:spin .7s linear infinite;margin-right:.3rem;}
@keyframes spin{to{transform:rotate(360deg)}}

/* Leaflet popup custom */
.custom-popup .leaflet-popup-content-wrapper{border-radius:10px;box-shadow:0 6px 20px rgba(0,0,0,.15);}
.custom-popup .leaflet-popup-content{margin:.7rem .9rem;font-family:'Nunito',sans-serif;font-size:.88rem;}
.popup-name{font-weight:800;color:var(--green-dark);font-size:.95rem;margin-bottom:.2rem;}
.popup-dist{color:var(--green-mid);font-weight:700;font-size:.82rem;}
.popup-addr{color:#7a9a7a;font-size:.78rem;margin-top:.18rem;}
.popup-nav{display:block;margin-top:.5rem;padding:.35rem .7rem;background:var(--green-mid);
  color:white;text-align:center;border-radius:7px;text-decoration:none;font-weight:700;font-size:.8rem;}
.popup-nav:hover{background:var(--green-dark);}
</style>
</head>
<body>

<nav class="navbar">
  <div class="nav-container">
    <div class="logo">🌿 PlantDoc AI</div>
    <ul class="nav-links">
      <li><a href="/">Home</a></li>
      <li><a href="/predict">Predict</a></li>
      <li><a href="/consultation">Expert Help</a></li>
      <li><a href="/crop-calendar">Crop Calendar</a></li>
      <li><a href="/diary">My Diary</a></li>
      <li><a href="/agri-shops" class="active">🏪 Agri Shops</a></li>
    </ul>
  </div>
</nav>

<div class="hero">
  <h1>🏪 Nearby Agri Shops</h1>
  <p>Find fertilizer, pesticide and seed shops near your location — free, no account needed</p>
</div>

<div class="page-body">

  <!-- Sidebar -->
  <div class="sidebar">
    <div class="search-area">
      <h3>🔍 Find Shops Near Me</h3>
      <button class="locate-btn" id="locateBtn" onclick="locateAndSearch()">
        📍 Use My Location
      </button>
      <div class="radius-row">
        <span class="radius-label">Search radius:</span>
        <select class="radius-select" id="radiusSelect" onchange="redoSearch()">
          <option value="1000">1 km</option>
          <option value="2000" selected>2 km</option>
          <option value="3000">3 km</option>
          <option value="5000">5 km</option>
          <option value="10000">10 km</option>
        </select>
      </div>
      <div class="type-chips" id="typeChips">
        <button class="type-chip active" data-type="all"     onclick="setType(this)">All Shops</button>
        <button class="type-chip"        data-type="agri"    onclick="setType(this)">🌱 Agri</button>
        <button class="type-chip"        data-type="seed"    onclick="setType(this)">🌾 Seeds</button>
        <button class="type-chip"        data-type="garden"  onclick="setType(this)">🪴 Garden</button>
        <button class="type-chip"        data-type="hardware"onclick="setType(this)">🔧 Hardware</button>
      </div>
    </div>

    <div class="status-bar" id="statusBar">
      <div class="status-dot" id="statusDot"></div>
      <span id="statusText">Click "Use My Location" to find shops near you</span>
    </div>

    <div class="shop-list" id="shopList">
      <div class="no-shops">
        <div class="ns-icon">📍</div>
        <div style="font-weight:700;color:var(--green-dark);margin-bottom:.4rem;">No shops loaded yet</div>
        <div style="font-size:.85rem;">Click the button above to find agricultural shops near your current location.</div>
      </div>
    </div>
  </div>

  <!-- Map -->
  <div id="map"></div>
</div>

<script>
// ── State ──────────────────────────────────────────────────────────────────
let map, userMarker, shopMarkers = [];
let userLat = null, userLng = null;
let allShops = [], activeType = 'all';

// ── Init Leaflet map (centered on India by default) ────────────────────────
map = L.map('map', { zoomControl: true }).setView([20.5937, 78.9629], 5);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© <a href="https://openstreetmap.org">OpenStreetMap</a> contributors',
  maxZoom: 19
}).addTo(map);

// Custom icons
const userIcon = L.divIcon({
  html: '<div style="background:#e63946;width:18px;height:18px;border-radius:50%;border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,.4);"></div>',
  iconSize:[18,18], iconAnchor:[9,9], className:''
});

function shopIcon(num, isActive) {
  const bg = isActive ? '#1b4332' : '#2d6a4f';
  return L.divIcon({
    html: `<div style="background:${bg};color:white;width:28px;height:28px;border-radius:50%;border:2.5px solid white;box-shadow:0 2px 8px rgba(0,0,0,.3);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;font-family:Nunito,sans-serif;">${num}</div>`,
    iconSize:[28,28], iconAnchor:[14,14], className:''
  });
}

// ── Set status ─────────────────────────────────────────────────────────────
function setStatus(text, state) {
  document.getElementById('statusText').textContent = text;
  const dot = document.getElementById('statusDot');
  dot.className = 'status-dot';
  if (state === 'loading') { dot.classList.add('orange','pulse'); }
  else if (state === 'ok')  { dot.classList.add('green'); }
  else if (state === 'err') { dot.classList.add('orange'); }
}

// ── Locate user ────────────────────────────────────────────────────────────
function locateAndSearch() {
  if (!navigator.geolocation) {
    setStatus('Geolocation not supported in this browser.', 'err');
    return;
  }
  const btn = document.getElementById('locateBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Getting location…';
  setStatus('Getting your location…', 'loading');

  navigator.geolocation.getCurrentPosition(
    pos => {
      userLat = pos.coords.latitude;
      userLng = pos.coords.longitude;
      btn.disabled = false;
      btn.innerHTML = '📍 Use My Location';
      placeUserMarker();
      fetchShops();
    },
    err => {
      btn.disabled = false;
      btn.innerHTML = '📍 Use My Location';
      const msgs = {
        1: 'Location permission denied. Please allow location access in your browser.',
        2: 'Could not detect location. Check GPS/network.',
        3: 'Location request timed out. Please try again.'
      };
      setStatus(msgs[err.code] || 'Location error.', 'err');
    },
    { timeout: 12000, maximumAge: 60000 }
  );
}

function placeUserMarker() {
  if (userMarker) map.removeLayer(userMarker);
  userMarker = L.marker([userLat, userLng], { icon: userIcon })
    .bindPopup('<div style="font-family:Nunito,sans-serif;font-weight:700;">📍 Your location</div>')
    .addTo(map);
  map.setView([userLat, userLng], 14);
}

// ── Fetch shops from Overpass API (OpenStreetMap) — free, no API key ───────
async function fetchShops() {
  const radius = parseInt(document.getElementById('radiusSelect').value);
  setStatus('Searching for shops…', 'loading');
  clearShopMarkers();

  // Overpass query: agri, garden, seed, hardware shops + pharmacies in radius
  const query = `
    [out:json][timeout:25];
    (
      node["shop"~"agrarian|garden|hardware|doityourself|seeds|farm"](around:${radius},${userLat},${userLng});
      node["amenity"="marketplace"](around:${radius},${userLat},${userLng});
      node["shop"="chemist"](around:${radius},${userLat},${userLng});
    );
    out body;
  `;

  try {
    const resp = await fetch('https://overpass-api.de/api/interpreter', {
      method: 'POST',
      body: query
    });
    if (!resp.ok) throw new Error('Overpass API error');
    const data  = await resp.json();
    allShops = processShops(data.elements);
    renderShops();
  } catch(err) {
    setStatus('Could not load shops. Check your internet connection.', 'err');
    console.error('Overpass error:', err);
  }
}

// ── Process OSM nodes into clean shop objects ──────────────────────────────
function processShops(elements) {
  return elements
    .filter(el => el.lat && el.lon)
    .map((el, i) => {
      const t   = el.tags || {};
      const lat = el.lat, lng = el.lon;
      const dist = haversine(userLat, userLng, lat, lng);

      // Determine shop type label
      const shopVal = (t.shop || '').toLowerCase();
      let typeLabel = 'General Shop', typeKey = 'agri';
      if (shopVal.match(/agrarian|farm/))        { typeLabel = 'Agriculture Shop'; typeKey = 'agri'; }
      else if (shopVal.match(/seeds?/))          { typeLabel = 'Seed Shop'; typeKey = 'seed'; }
      else if (shopVal.match(/garden/))          { typeLabel = 'Garden Centre'; typeKey = 'garden'; }
      else if (shopVal.match(/hardware|diy/))    { typeLabel = 'Hardware Store'; typeKey = 'hardware'; }
      else if (shopVal.match(/chemist/))         { typeLabel = 'Chemist/Pharmacy'; typeKey = 'agri'; }
      else if (t.amenity === 'marketplace')      { typeLabel = 'Marketplace'; typeKey = 'agri'; }

      // Build address
      const addr = [t['addr:housenumber'], t['addr:street'], t['addr:city']]
        .filter(Boolean).join(', ') || t['addr:full'] || '';

      // Tags/products
      const tags = [];
      if (t.fertilizer === 'yes' || t.sells_fertilizer === 'yes') tags.push('Fertilizer');
      if (t.pesticide  === 'yes' || t.sells_pesticides  === 'yes') tags.push('Pesticide');
      if (shopVal.includes('seed'))    tags.push('Seeds');
      if (shopVal.includes('agrarian')) tags.push('Farm Supplies');

      return {
        id: el.id, num: i+1, lat, lng, dist,
        name:      t.name || t['name:en'] || 'Agricultural Shop',
        typeLabel, typeKey, addr,
        phone:     t.phone || t['contact:phone'] || '',
        hours:     t.opening_hours || '',
        website:   t.website || t['contact:website'] || '',
        tags
      };
    })
    .sort((a, b) => a.dist - b.dist)
    .slice(0, 30); // max 30 results
}

// ── Haversine distance in meters ───────────────────────────────────────────
function haversine(lat1, lon1, lat2, lon2) {
  const R = 6371000;
  const dLat = (lat2-lat1) * Math.PI/180;
  const dLon = (lon2-lon1) * Math.PI/180;
  const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;
  return Math.round(R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)));
}

function distLabel(m) {
  return m < 1000 ? `${m} m away` : `${(m/1000).toFixed(1)} km away`;
}

// ── Render shop list + map markers ────────────────────────────────────────
function renderShops() {
  const filtered = activeType === 'all'
    ? allShops
    : allShops.filter(s => s.typeKey === activeType);

  setStatus(
    filtered.length
      ? `Found ${filtered.length} shop${filtered.length!==1?'s':''} nearby`
      : 'No shops found in this area — try increasing the radius',
    filtered.length ? 'ok' : 'err'
  );

  clearShopMarkers();

  if (!filtered.length) {
    document.getElementById('shopList').innerHTML = `
      <div class="no-shops">
        <div class="ns-icon">🔍</div>
        <div style="font-weight:700;color:var(--green-dark);margin-bottom:.4rem;">No shops found</div>
        <div style="font-size:.83rem;">Try increasing the search radius or select "All Shops".</div>
      </div>`;
    return;
  }

  // Build list HTML
  document.getElementById('shopList').innerHTML = filtered.map((s, idx) => `
    <div class="shop-card" id="card-${s.id}" onclick="focusShop('${s.id}')">
      <div class="shop-num">${idx+1}</div>
      <div class="shop-name">${esc(s.name)}</div>
      <div class="shop-type">${s.typeLabel}</div>
      <div class="shop-dist">📍 ${distLabel(s.dist)}</div>
      ${s.addr ? `<div class="shop-addr">${esc(s.addr)}</div>` : ''}
      ${s.phone ? `<div class="shop-addr">📞 ${esc(s.phone)}</div>` : ''}
      ${s.hours ? `<div class="shop-addr">🕐 ${esc(s.hours)}</div>` : ''}
      ${s.tags.length ? `<div class="shop-tags">${s.tags.map(t=>`<span class="shop-tag">${t}</span>`).join('')}</div>` : ''}
      <div class="shop-actions">
        <a class="shop-btn primary"
           href="https://www.google.com/maps/dir/?api=1&destination=${s.lat},${s.lng}"
           target="_blank" onclick="event.stopPropagation()">🗺 Directions</a>
        <a class="shop-btn"
           href="https://www.google.com/maps/search/?api=1&query=${s.lat},${s.lng}"
           target="_blank" onclick="event.stopPropagation()">📌 View on Maps</a>
        ${s.phone ? `<a class="shop-btn" href="tel:${s.phone}" onclick="event.stopPropagation()">📞 Call</a>` : ''}
      </div>
    </div>`).join('');

  // Add map markers
  filtered.forEach((s, idx) => {
    const marker = L.marker([s.lat, s.lng], { icon: shopIcon(idx+1, false) })
      .bindPopup(`
        <div class="popup-name">${esc(s.name)}</div>
        <div class="popup-dist">${distLabel(s.dist)}</div>
        ${s.addr ? `<div class="popup-addr">${esc(s.addr)}</div>` : ''}
        <a class="popup-nav" href="https://www.google.com/maps/dir/?api=1&destination=${s.lat},${s.lng}" target="_blank">🗺 Get Directions</a>
      `, { className: 'custom-popup' })
      .addTo(map);

    marker.on('click', () => {
      focusShop(s.id);
      document.getElementById(`card-${s.id}`)?.scrollIntoView({ behavior:'smooth', block:'nearest' });
    });
    shopMarkers.push({ id: s.id, marker });
  });

  // Fit map to show all results + user
  const allPoints = [[userLat, userLng], ...filtered.map(s => [s.lat, s.lng])];
  map.fitBounds(L.latLngBounds(allPoints), { padding: [30, 30] });
}

// ── Focus a shop (highlight card + open popup) ─────────────────────────────
function focusShop(id) {
  // Highlight card
  document.querySelectorAll('.shop-card').forEach(c => c.classList.remove('active'));
  document.getElementById(`card-${id}`)?.classList.add('active');

  // Open popup on marker
  const found = shopMarkers.find(m => String(m.id) === String(id));
  if (found) {
    map.setView(found.marker.getLatLng(), 16, { animate: true });
    found.marker.openPopup();
  }
}

function clearShopMarkers() {
  shopMarkers.forEach(m => map.removeLayer(m.marker));
  shopMarkers = [];
}

// ── Type filter ────────────────────────────────────────────────────────────
function setType(btn) {
  document.querySelectorAll('.type-chip').forEach(c => c.classList.remove('active'));
  btn.classList.add('active');
  activeType = btn.dataset.type;
  if (allShops.length) renderShops();
}

// ── Redo search on radius change ───────────────────────────────────────────
function redoSearch() {
  if (userLat !== null) fetchShops();
}

function esc(t) {
  return String(t||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
</script>
</body>
</html>"""