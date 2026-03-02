"""
consultation.py — AI Expert Consultation (v2)
New in v2: Multilingual Voice Replies (TTS), Save to Diary button
Replace your existing consultation.py with this file.

Requires diary.py to be running (for Save to Diary).
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, HTMLResponse
import os, logging, httpx

logger = logging.getLogger(__name__)
consultation_router = APIRouter()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

LANGUAGE_INSTRUCTIONS = {
    "english": "Respond in English.",
    "hindi":   "हमेशा हिंदी में जवाब दें। सरल और आसान हिंदी इस्तेमाल करें।",
    "marathi": "नेहमी मराठीत उत्तर द्या. सोपी मराठी वापरा.",
    "telugu":  "దయచేసి తెలుగులో సమాధానం ఇవ్వండి.",
    "tamil":   "தயவுசெய்து தமிழில் பதில் சொல்லுங்கள்.",
    "kannada": "ದಯವಿಟ್ಟು ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರಿಸಿ.",
    "bengali": "দয়া করে বাংলায় উত্তর দিন।",
    "gujarati":"કૃપા કરીને ગુજરાતીમાં જવાબ આપો.",
    "punjabi": "ਕਿਰਪਾ ਕਰਕੇ ਪੰਜਾਬੀ ਵਿੱਚ ਜਵਾਬ ਦਿਓ।",
}

BASE_SYSTEM_PROMPT = """You are a friendly agricultural expert assistant called "AgriDoc" helping farmers in India and across the world understand plant diseases and farming problems.

IMPORTANT RULES:
1. Always use VERY simple, plain language — imagine you are talking to a farmer with no technical background
2. Avoid scientific jargon. If you must use a technical term, immediately explain it in brackets
3. Give PRACTICAL, actionable advice — what to buy, where to apply, how much to use
4. Be warm, patient, and encouraging. Farmers work hard and need support, not lectures
5. When recommending treatments, always mention:
   - Cheap/local options first
   - Organic alternatives when possible
   - Safety precautions (very important for farmers handling chemicals)
6. Keep answers concise but complete — use bullet points for steps
7. If you do not know something, say so honestly and recommend seeing a local agricultural officer (Krishi Sevak / KVK)
8. Always end with an encouraging note

When analyzing a plant image:
- Describe what you see on the leaves/plant clearly
- Identify any visible disease symptoms
- Suggest likely disease based on visual signs
- Give immediate treatment steps

You know about these diseases the app detects:
- Anthracnose: dark spots, fungal, use copper fungicide
- Powdery Mildew: white powder on leaves, use sulfur spray or milk solution
- Leaf Crinkle: viral, spread by insects, remove infected plants
- Yellow Mosaic: viral, yellow patches, control whitefly insects
- Healthy: no disease, keep up good practices"""


@consultation_router.get('/consultation')
async def consultation_page():
    return HTMLResponse(content=_html())


@consultation_router.post('/ask-expert')
async def ask_expert(request: Request):
    try:
        body            = await request.json()
        user_message    = body.get("message", "").strip()
        history         = body.get("history", [])
        disease_context = body.get("disease_context", "")
        language        = body.get("language", "english").lower()
        image_base64    = body.get("image_base64", "")

        if not user_message and not image_base64:
            return JSONResponse({"status":"error","detail":"Please type a message or upload a photo."}, status_code=400)
        if not OPENAI_API_KEY:
            return JSONResponse({"status":"error","detail":"OPENAI_API_KEY not set."}, status_code=500)

        lang_instr    = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["english"])
        system_prompt = BASE_SYSTEM_PROMPT + f"\n\nLANGUAGE INSTRUCTION: {lang_instr}"
        messages      = [{"role":"system","content":system_prompt}]

        for turn in history[-10:]:
            if turn.get("role") in ("user","assistant") and turn.get("content"):
                messages.append({"role":turn["role"],"content":turn["content"]})

        display_msg = user_message or "Please analyze this plant image."
        if disease_context:
            display_msg = f"[Plant scan context: {disease_context}]\n\nMy question: {display_msg}"

        if image_base64:
            if "," in image_base64:
                header, raw_b64 = image_base64.split(",",1)
                mt = "image/png" if "png" in header else ("image/webp" if "webp" in header else "image/jpeg")
            else:
                raw_b64, mt = image_base64, "image/jpeg"
            user_content = [
                {"type":"image_url","image_url":{"url":f"data:{mt};base64,{raw_b64}","detail":"low"}},
                {"type":"text","text":display_msg}
            ]
        else:
            user_content = display_msg

        messages.append({"role":"user","content":user_content})

        async with httpx.AsyncClient(timeout=40.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization":f"Bearer {OPENAI_API_KEY}","Content-Type":"application/json"},
                json={"model":"gpt-4o-mini","max_tokens":1024,"messages":messages}
            )

        if resp.status_code != 200:
            err = resp.json().get("error",{}).get("message", resp.text)
            return JSONResponse({"status":"error","detail":f"OpenAI error: {err}"}, status_code=500)

        reply = resp.json()["choices"][0]["message"]["content"]
        return JSONResponse({"status":"success","reply":reply})

    except httpx.TimeoutException:
        return JSONResponse({"status":"error","detail":"Request timed out."}, status_code=504)
    except Exception as e:
        logger.error(f"Consultation error: {e}", exc_info=True)
        return JSONResponse({"status":"error","detail":str(e)}, status_code=500)


def _html() -> str:
    return r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Expert Consultation – PlantDoc AI</title>
<link href="https://fonts.googleapis.com/css2?family=Lora:wght@500;600;700&family=Source+Sans+3:wght@300;400;500;600&display=swap" rel="stylesheet"/>
<style>
:root{--soil:#2d1b0e;--bark:#5c3d1e;--moss:#3a6b35;--leaf:#5a9e4f;--sprout:#8dc87b;
  --mist:#e8f5e3;--cream:#faf7f2;--fog:#d4e8cc;--clay:#c4825a;--red:#e53e3e;--sky:#ebf8ff;}
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Source Sans 3',sans-serif;background:var(--cream);min-height:100vh;color:var(--soil);}
.navbar{background:rgba(250,247,242,.96);backdrop-filter:blur(12px);padding:1rem 2rem;box-shadow:0 2px 20px rgba(45,27,14,.08);position:sticky;top:0;z-index:100;}
.nav-container{max-width:1200px;margin:0 auto;display:flex;justify-content:space-between;align-items:center;}
.logo{font-family:'Lora',serif;font-size:1.4rem;color:var(--moss);font-weight:700;}
.nav-links{display:flex;list-style:none;gap:1.2rem;flex-wrap:wrap;}
.nav-links a{text-decoration:none;color:var(--bark);font-weight:500;padding:.4rem .8rem;border-radius:6px;transition:all .25s;font-size:.9rem;}
.nav-links a:hover,.nav-links a.active{background:var(--moss);color:white;}
.page-header{background:linear-gradient(135deg,var(--moss) 0%,#2a5225 100%);color:white;padding:2rem 2rem 1.5rem;text-align:center;}
.page-header h1{font-family:'Lora',serif;font-size:1.9rem;margin-bottom:.3rem;}
.page-header p{opacity:.88;font-size:1rem;}
.badge-row{display:flex;gap:.6rem;justify-content:center;margin-top:.9rem;flex-wrap:wrap;}
.badge{background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.3);border-radius:20px;padding:.25rem .8rem;font-size:.8rem;}
.page-wrapper{max-width:1100px;margin:0 auto;padding:1.5rem;display:grid;grid-template-columns:300px 1fr;gap:1.5rem;}
@media(max-width:780px){.page-wrapper{grid-template-columns:1fr;}.sidebar{order:2;}.chat-panel{order:1;}}
.sidebar{display:flex;flex-direction:column;gap:1rem;}
.card{background:white;border-radius:14px;box-shadow:0 4px 20px rgba(45,27,14,.07);overflow:hidden;}
.card-header{background:var(--mist);padding:.8rem 1.1rem;border-bottom:1px solid var(--fog);font-family:'Lora',serif;font-weight:600;font-size:.92rem;color:var(--moss);}
.card-body{padding:.9rem 1.1rem;}
.lang-select{width:100%;padding:.6rem .85rem;border:1.5px solid var(--fog);border-radius:8px;font-family:'Source Sans 3',sans-serif;font-size:.9rem;color:var(--soil);background:white;cursor:pointer;}
.lang-select:focus{outline:none;border-color:var(--leaf);}
.lang-hint{font-size:.76rem;color:#9aab8e;margin-top:.35rem;}
/* TTS toggle */
.tts-row{display:flex;align-items:center;gap:.7rem;margin-top:.7rem;padding:.6rem .8rem;background:var(--mist);border-radius:8px;border:1px solid var(--fog);}
.tts-label{font-size:.88rem;color:var(--soil);flex:1;}
.tts-toggle{position:relative;width:40px;height:22px;flex-shrink:0;}
.tts-toggle input{opacity:0;width:0;height:0;}
.tts-slider{position:absolute;inset:0;background:#ccc;border-radius:22px;cursor:pointer;transition:.3s;}
.tts-slider:before{content:'';position:absolute;width:16px;height:16px;left:3px;bottom:3px;background:white;border-radius:50%;transition:.3s;}
input:checked + .tts-slider{background:var(--leaf);}
input:checked + .tts-slider:before{transform:translateX(18px);}
.quick-btn{display:block;width:100%;text-align:left;background:var(--mist);border:1.5px solid var(--fog);color:var(--soil);padding:.55rem .8rem;border-radius:8px;font-size:.86rem;cursor:pointer;margin-bottom:.4rem;transition:all .2s;font-family:'Source Sans 3',sans-serif;}
.quick-btn:hover{background:var(--fog);border-color:var(--leaf);color:var(--moss);transform:translateX(3px);}
.quick-btn:last-child{margin-bottom:0;}
.context-area{width:100%;min-height:72px;padding:.65rem;border:1.5px solid var(--fog);border-radius:8px;font-family:'Source Sans 3',sans-serif;font-size:.83rem;color:var(--soil);resize:vertical;background:#fdfcfa;}
.context-area:focus{outline:none;border-color:var(--leaf);}
.context-label{font-size:.8rem;color:#6b7c61;margin-bottom:.35rem;display:block;}
.context-hint{font-size:.76rem;color:#9aab8e;margin-top:.35rem;}
.expert-contact{display:flex;gap:.7rem;align-items:flex-start;margin-bottom:.65rem;}
.expert-avatar{width:38px;height:38px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:1.2rem;background:var(--mist);}
.expert-name{font-weight:600;font-size:.88rem;color:var(--soil);}
.expert-role{font-size:.76rem;color:#7a8f6e;}
.expert-phone{font-size:.78rem;color:var(--moss);margin-top:.12rem;}
.helpline-btn{display:block;width:100%;padding:.6rem;background:linear-gradient(135deg,var(--leaf),var(--moss));color:white;border:none;border-radius:8px;font-family:'Source Sans 3',sans-serif;font-weight:600;font-size:.88rem;cursor:pointer;text-align:center;text-decoration:none;margin-top:.5rem;transition:opacity .2s;}
.helpline-btn:hover{opacity:.88;}
.chat-panel{display:flex;flex-direction:column;}
.chat-card{background:white;border-radius:14px;box-shadow:0 4px 20px rgba(45,27,14,.07);display:flex;flex-direction:column;height:680px;}
.chat-topbar{padding:.9rem 1.3rem;background:linear-gradient(135deg,var(--moss) 0%,#2a5225 100%);border-radius:14px 14px 0 0;display:flex;align-items:center;gap:.8rem;}
.bot-avatar{width:42px;height:42px;border-radius:50%;background:rgba(255,255,255,.2);display:flex;align-items:center;justify-content:center;font-size:1.4rem;flex-shrink:0;}
.bot-name{font-family:'Lora',serif;color:white;font-weight:600;font-size:.98rem;}
.bot-status{color:rgba(255,255,255,.75);font-size:.78rem;display:flex;align-items:center;gap:.3rem;}
.status-dot{width:6px;height:6px;border-radius:50%;background:var(--sprout);display:inline-block;animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.topbar-actions{margin-left:auto;display:flex;gap:.5rem;}
.clear-btn,.save-all-btn{background:none;border:1px solid rgba(255,255,255,.35);color:rgba(255,255,255,.8);border-radius:6px;padding:.28rem .65rem;font-size:.76rem;cursor:pointer;font-family:'Source Sans 3',sans-serif;transition:all .2s;}
.clear-btn:hover,.save-all-btn:hover{border-color:white;color:white;}
.save-all-btn{background:rgba(255,255,255,.15);}
.chat-messages{flex:1;overflow-y:auto;padding:1.1rem;display:flex;flex-direction:column;gap:.9rem;}
.chat-messages::-webkit-scrollbar{width:4px;}
.chat-messages::-webkit-scrollbar-thumb{background:var(--fog);border-radius:4px;}
.msg{display:flex;gap:.5rem;max-width:90%;}
.msg.user{flex-direction:row-reverse;align-self:flex-end;}
.msg.bot{align-self:flex-start;}
.msg-avatar{width:30px;height:30px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:.95rem;}
.msg.bot .msg-avatar{background:var(--mist);}
.msg.user .msg-avatar{background:var(--soil);}
.msg-content{display:flex;flex-direction:column;}
.msg-bubble{padding:.7rem .95rem;border-radius:13px;font-size:.9rem;line-height:1.55;}
.msg.bot .msg-bubble{background:var(--mist);color:var(--soil);border-bottom-left-radius:3px;}
.msg.user .msg-bubble{background:linear-gradient(135deg,var(--moss),#2a5225);color:white;border-bottom-right-radius:3px;}
.msg-actions{display:flex;gap:.4rem;margin-top:.3rem;}
.msg.user .msg-actions{justify-content:flex-end;}
.action-btn{background:none;border:1px solid var(--fog);color:#7a9a6a;border-radius:5px;padding:.18rem .5rem;font-size:.72rem;cursor:pointer;font-family:'Source Sans 3',sans-serif;transition:all .2s;display:flex;align-items:center;gap:.25rem;}
.action-btn:hover{background:var(--mist);border-color:var(--leaf);color:var(--moss);}
.action-btn.speaking{background:#e8f5e3;border-color:var(--leaf);color:var(--moss);}
.action-btn.saved{background:#d4f0d4;border-color:var(--moss);color:var(--moss);}
.msg-time{font-size:.68rem;opacity:.5;}
.msg.bot .msg-time{text-align:left;}
.msg.user .msg-time{text-align:right;}
.msg-bubble img.sent-img{max-width:160px;border-radius:7px;display:block;margin-bottom:.4rem;}
.typing-bubble{display:flex;align-items:center;gap:4px;padding:.7rem .95rem;}
.typing-dot{width:7px;height:7px;border-radius:50%;background:var(--leaf);animation:tb 1.2s infinite;}
.typing-dot:nth-child(2){animation-delay:.2s;}
.typing-dot:nth-child(3){animation-delay:.4s;}
@keyframes tb{0%,80%,100%{transform:translateY(0)}40%{transform:translateY(-6px)}}
.chat-input-area{padding:.9rem 1.1rem;border-top:1px solid var(--fog);background:#fdfcfa;border-radius:0 0 14px 14px;}
.image-preview-strip{display:none;align-items:center;gap:.6rem;margin-bottom:.55rem;background:var(--mist);border-radius:8px;padding:.45rem .7rem;}
.image-preview-strip.visible{display:flex;}
.preview-thumb{width:40px;height:40px;object-fit:cover;border-radius:6px;border:1.5px solid var(--fog);}
.preview-name{font-size:.8rem;color:var(--soil);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.remove-img-btn{background:none;border:none;color:var(--clay);font-size:1rem;cursor:pointer;}
.voice-status{font-size:.78rem;color:var(--red);margin-bottom:.3rem;text-align:center;display:none;font-weight:600;}
.voice-status.visible{display:block;}
.input-row{display:flex;gap:.45rem;align-items:flex-end;}
.chat-input{flex:1;padding:.7rem .95rem;border:1.5px solid var(--fog);border-radius:9px;font-family:'Source Sans 3',sans-serif;font-size:.9rem;color:var(--soil);resize:none;max-height:100px;background:white;transition:border-color .2s;}
.chat-input:focus{outline:none;border-color:var(--leaf);box-shadow:0 0 0 3px rgba(90,158,79,.09);}
.icon-btn{width:40px;height:40px;border-radius:8px;flex-shrink:0;border:1.5px solid var(--fog);background:white;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:1.1rem;transition:all .2s;color:var(--bark);}
.icon-btn:hover{background:var(--mist);border-color:var(--leaf);color:var(--moss);}
.icon-btn.recording{background:#fff0f0;border-color:var(--red);color:var(--red);animation:rp 1s infinite;}
@keyframes rp{0%,100%{box-shadow:0 0 0 0 rgba(229,62,62,.4)}50%{box-shadow:0 0 0 6px rgba(229,62,62,0)}}
.send-btn{width:40px;height:40px;border-radius:8px;flex-shrink:0;background:linear-gradient(135deg,var(--leaf),var(--moss));color:white;border:none;cursor:pointer;font-size:1rem;display:flex;align-items:center;justify-content:center;transition:all .2s;}
.send-btn:hover{transform:scale(1.06);opacity:.9;}
.send-btn:disabled{opacity:.45;cursor:not-allowed;transform:none;}
.input-hint{font-size:.72rem;color:#9aab8e;margin-top:.35rem;text-align:center;}
.welcome-card{background:linear-gradient(135deg,var(--mist),var(--fog));border:1.5px solid var(--fog);border-radius:12px;padding:1.1rem;text-align:center;}
.welcome-card .wi{font-size:2rem;margin-bottom:.4rem;}
.welcome-card h3{font-family:'Lora',serif;color:var(--moss);margin-bottom:.25rem;}
.welcome-card p{font-size:.86rem;color:#5a7050;line-height:1.5;}
.msg-bubble ul{padding-left:1.15rem;margin:.35rem 0;}
.msg-bubble li{margin-bottom:.2rem;}
.msg-bubble strong{color:var(--moss);}
.msg.user .msg-bubble strong{color:#c8f0b8;}
/* Save success toast */
.toast{position:fixed;bottom:2rem;right:2rem;background:var(--moss);color:white;padding:.75rem 1.3rem;
  border-radius:10px;font-size:.88rem;font-weight:600;box-shadow:0 4px 20px rgba(0,0,0,.2);
  z-index:999;opacity:0;transform:translateY(10px);transition:all .3s;pointer-events:none;}
.toast.show{opacity:1;transform:translateY(0);}
</style>
</head>
<body>

<nav class="navbar">
  <div class="nav-container">
    <div class="logo">🌿 PlantDoc AI</div>
    <ul class="nav-links">
      <li><a href="/">Home</a></li>
      <li><a href="/predict">Predict</a></li>
      <li><a href="/records-page">Records</a></li>
      <li><a href="/webcam">Live Cam</a></li>
      <li><a href="/consultation" class="active">Expert Help</a></li>
      <li><a href="/crop-calendar">Crop Calendar</a></li>
      <li><a href="/diary">My Diary</a></li>
    </ul>
  </div>
</nav>

<div class="page-header">
  <h1>🌾 Ask an Agriculture Expert</h1>
  <p>Voice, photo or text — get simple advice in your own language</p>
  <div class="badge-row">
    <span class="badge">🎤 Voice Input</span>
    <span class="badge">🔊 Voice Replies</span>
    <span class="badge">📸 Photo Analysis</span>
    <span class="badge">🌐 9 Languages</span>
    <span class="badge">📔 Save to Diary</span>
  </div>
</div>

<div class="page-wrapper">
  <aside class="sidebar">

    <div class="card">
      <div class="card-header">🌐 Language &amp; Voice</div>
      <div class="card-body">
        <select class="lang-select" id="languageSelect">
          <option value="english">🇬🇧 English</option>
          <option value="hindi">🇮🇳 हिंदी (Hindi)</option>
          <option value="marathi">🟠 मराठी (Marathi)</option>
          <option value="telugu">🟡 తెలుగు (Telugu)</option>
          <option value="tamil">🟢 தமிழ் (Tamil)</option>
          <option value="kannada">🔵 ಕನ್ನಡ (Kannada)</option>
          <option value="bengali">🟣 বাংলা (Bengali)</option>
          <option value="gujarati">🔶 ગુજરાતી (Gujarati)</option>
          <option value="punjabi">🔷 ਪੰਜਾਬੀ (Punjabi)</option>
        </select>
        <p class="lang-hint">AgriDoc will reply in the language you choose</p>
        <div class="tts-row">
          <span class="tts-label">🔊 Read replies aloud</span>
          <label class="tts-toggle">
            <input type="checkbox" id="ttsToggle" checked/>
            <span class="tts-slider"></span>
          </label>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">💬 Quick Questions</div>
      <div class="card-body">
        <button class="quick-btn" onclick="sendQuick(this)">🍂 My leaves are turning yellow</button>
        <button class="quick-btn" onclick="sendQuick(this)">⚪ White powder on my leaves</button>
        <button class="quick-btn" onclick="sendQuick(this)">🔴 Dark spots on my plant leaves</button>
        <button class="quick-btn" onclick="sendQuick(this)">🐛 Insects damaging my crop</button>
        <button class="quick-btn" onclick="sendQuick(this)">💊 Cheapest treatment for plant disease?</button>
        <button class="quick-btn" onclick="sendQuick(this)">🌿 Organic treatment without chemicals?</button>
        <button class="quick-btn" onclick="sendQuick(this)">💧 How often should I water my plants?</button>
        <button class="quick-btn" onclick="sendQuick(this)">📅 Best time to spray pesticide?</button>
      </div>
    </div>

    <div class="card">
      <div class="card-header">📋 Paste Scan Result</div>
      <div class="card-body">
        <span class="context-label">Paste your Predict page result here for specific advice:</span>
        <textarea class="context-area" id="diseaseContext" placeholder="e.g. Disease: Powdery Mildew, Severity: Medium, Confidence: 87%..."></textarea>
        <p class="context-hint">ℹ️ Gives AgriDoc full context about your plant scan</p>
      </div>
    </div>

    <div class="card">
      <div class="card-header">📞 Real Expert Contacts</div>
      <div class="card-body">
        <div class="expert-contact">
          <div class="expert-avatar">👨‍🌾</div>
          <div><div class="expert-name">Kisan Call Centre</div><div class="expert-role">Ministry of Agriculture, India</div><div class="expert-phone">📞 1800-180-1551 (Free)</div></div>
        </div>
        <div class="expert-contact">
          <div class="expert-avatar">🏫</div>
          <div><div class="expert-name">Local KVK Centre</div><div class="expert-role">Krishi Vigyan Kendra</div><div class="expert-phone">🌐 kvk.icar.gov.in</div></div>
        </div>
        <div class="expert-contact">
          <div class="expert-avatar">🌾</div>
          <div><div class="expert-name">PM Kisan Helpline</div><div class="expert-role">Farmer support &amp; welfare</div><div class="expert-phone">📞 155261</div></div>
        </div>
        <a href="tel:18001801551" class="helpline-btn">📞 Call Kisan Helpline</a>
      </div>
    </div>

  </aside>

  <div class="chat-panel">
    <div class="chat-card">
      <div class="chat-topbar">
        <div class="bot-avatar">🌱</div>
        <div>
          <div class="bot-name">AgriDoc — Your Farm Expert</div>
          <div class="bot-status"><span class="status-dot"></span> Online — Ready to help</div>
        </div>
        <div class="topbar-actions">
          <button class="save-all-btn" onclick="saveFullChat()">📔 Save to Diary</button>
          <button class="clear-btn" onclick="clearChat()">🗑 Clear</button>
        </div>
      </div>

      <div class="chat-messages" id="chatMessages">
        <div class="welcome-card">
          <div class="wi">🌾</div>
          <h3>Namaste! I'm AgriDoc</h3>
          <p>Ask me anything about your plants.<br><br>
          <strong>🎤 Speak</strong> — tap the mic and talk in your language<br>
          <strong>📸 Photo</strong> — upload a leaf photo and I'll analyse it<br>
          <strong>🔊 Voice replies</strong> — I'll read my answer aloud (toggle on left)<br>
          <strong>📔 Save to Diary</strong> — save any conversation for future reference</p>
        </div>
      </div>

      <div class="chat-input-area">
        <div class="image-preview-strip" id="imagePreviewStrip">
          <img src="" id="previewThumb" class="preview-thumb" alt="preview"/>
          <span class="preview-name" id="previewName">photo.jpg</span>
          <button class="remove-img-btn" onclick="removeImage()">✕</button>
        </div>
        <div class="voice-status" id="voiceStatus">🎤 Listening… speak now</div>
        <div class="input-row">
          <button class="icon-btn" id="voiceBtn" onclick="toggleVoice()" title="Voice input">🎤</button>
          <button class="icon-btn" onclick="document.getElementById('photoInput').click()" title="Upload photo">📸</button>
          <input type="file" id="photoInput" accept="image/*" style="display:none" onchange="handlePhoto(event)"/>
          <textarea class="chat-input" id="chatInput" placeholder="Type, speak 🎤 or upload a photo 📸…" rows="2"></textarea>
          <button class="send-btn" id="sendBtn" onclick="sendMessage()">&#9658;</button>
        </div>
        <p class="input-hint">Enter to send · Shift+Enter new line · 🎤 Voice: Chrome/Edge · 🔊 Replies read aloud when enabled</p>
      </div>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
// ── State ──────────────────────────────────────────────────────────────────
let chatHistory=[], selectedImage=null, recognition=null, isRecording=false;
let currentUtterance=null;

const chatMessages = document.getElementById('chatMessages');
const chatInput    = document.getElementById('chatInput');
const sendBtn      = document.getElementById('sendBtn');
const voiceBtn     = document.getElementById('voiceBtn');
const voiceStatus  = document.getElementById('voiceStatus');
const imageStrip   = document.getElementById('imagePreviewStrip');

// Pre-fill from URL params (set by Predict page "Ask Expert" button)
window.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const disease = params.get('disease');
  const details = params.get('details');
  if (disease) {
    document.getElementById('diseaseContext').value = details || disease;
    appendMessage('bot',
      `I can see you just scanned your plant and detected **${disease}**.\n\nI already have your scan result loaded in the context box on the left. What would you like to know about this? You can ask me:\n- How to treat ${disease}\n- What caused it\n- How to prevent it from spreading\n- Organic treatment options`,
      null, false);
  }
});

chatInput.addEventListener('keydown', e => {
  if (e.key==='Enter' && !e.shiftKey){e.preventDefault();sendMessage();}
});

// ── Helpers ────────────────────────────────────────────────────────────────
function getTime(){return new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});}

function formatText(t){
  return t
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>')
    .replace(/\*(.*?)\*/g,'<em>$1</em>')
    .replace(/^[-*•]\s(.+)$/gm,'<li>$1</li>')
    .replace(/(<li>.*?<\/li>\n?)+/gs,m=>`<ul>${m}</ul>`)
    .replace(/\n/g,'<br>');
}

function showToast(msg){
  const t=document.getElementById('toast');
  t.textContent=msg; t.classList.add('show');
  setTimeout(()=>t.classList.remove('show'),3000);
}

// ── Message rendering ──────────────────────────────────────────────────────
function appendMessage(role, text, imgUrl, isTyping){
  const wrap=document.createElement('div');
  wrap.className='msg '+role;
  if(isTyping) wrap.id='typing-indicator';

  const av=document.createElement('div');
  av.className='msg-avatar';
  av.textContent=role==='bot'?'🌱':'👨‍🌾';

  const content=document.createElement('div');
  content.className='msg-content';

  if(isTyping){
    content.innerHTML='<div class="msg-bubble"><div class="typing-bubble"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div></div>';
  } else {
    let html='';
    if(imgUrl) html+=`<img src="${imgUrl}" class="sent-img" alt="plant"/>`;
    html+=formatText(text);
    content.innerHTML=`<div class="msg-bubble">${html}</div><div class="msg-time">${getTime()}</div>`;

    // Action buttons for bot messages
    if(role==='bot'){
      const actions=document.createElement('div');
      actions.className='msg-actions';

      const speakBtn=document.createElement('button');
      speakBtn.className='action-btn';
      speakBtn.innerHTML='🔊 Read aloud';
      speakBtn.onclick=()=>speakText(text, speakBtn);

      const saveBtn=document.createElement('button');
      saveBtn.className='action-btn';
      saveBtn.innerHTML='📔 Save to Diary';
      saveBtn.onclick=()=>saveSingleReply(text, saveBtn);

      actions.appendChild(speakBtn);
      actions.appendChild(saveBtn);
      content.appendChild(actions);
    }
  }

  wrap.appendChild(av);
  wrap.appendChild(content);
  chatMessages.appendChild(wrap);
  chatMessages.scrollTop=chatMessages.scrollHeight;
  return wrap;
}

// ── TTS — Voice Replies (FREE browser API) ─────────────────────────────────
const TTS_LANG_MAP={
  english:'en-IN', hindi:'hi-IN', marathi:'mr-IN', telugu:'te-IN',
  tamil:'ta-IN', kannada:'kn-IN', bengali:'bn-IN', gujarati:'gu-IN', punjabi:'pa-Guru-IN'
};

function speakText(text, btn){
  if(!window.speechSynthesis){alert('Voice reading not supported in this browser. Use Chrome or Edge.');return;}
  // If already speaking this, stop
  if(currentUtterance && btn.classList.contains('speaking')){
    window.speechSynthesis.cancel();
    btn.innerHTML='🔊 Read aloud';
    btn.classList.remove('speaking');
    currentUtterance=null;
    return;
  }
  // Cancel any ongoing speech
  window.speechSynthesis.cancel();
  // Reset all other speak buttons
  document.querySelectorAll('.action-btn.speaking').forEach(b=>{b.innerHTML='🔊 Read aloud';b.classList.remove('speaking');});

  // Clean text of markdown/HTML for speech
  const cleanText=text.replace(/\*\*(.*?)\*\*/g,'$1').replace(/\*(.*?)\*/g,'$1')
    .replace(/[<>]/g,'').replace(/[-•]/g,'').trim();

  const lang=document.getElementById('languageSelect').value;
  const utt=new SpeechSynthesisUtterance(cleanText);
  utt.lang=TTS_LANG_MAP[lang]||'en-IN';
  utt.rate=0.9;
  utt.pitch=1;

  // Try to find a matching voice
  const voices=window.speechSynthesis.getVoices();
  const match=voices.find(v=>v.lang.startsWith(utt.lang.split('-')[0]));
  if(match) utt.voice=match;

  utt.onstart=()=>{btn.innerHTML='⏹ Stop reading';btn.classList.add('speaking');};
  utt.onend=()=>{btn.innerHTML='🔊 Read aloud';btn.classList.remove('speaking');currentUtterance=null;};
  utt.onerror=()=>{btn.innerHTML='🔊 Read aloud';btn.classList.remove('speaking');currentUtterance=null;};

  currentUtterance=utt;
  window.speechSynthesis.speak(utt);
}

function autoSpeak(text){
  if(!document.getElementById('ttsToggle').checked) return;
  if(!window.speechSynthesis) return;
  const lang=document.getElementById('languageSelect').value;
  const cleanText=text.replace(/\*\*(.*?)\*\*/g,'$1').replace(/\*(.*?)\*/g,'$1')
    .replace(/[<>]/g,'').replace(/[-•]/g,'').trim();
  const utt=new SpeechSynthesisUtterance(cleanText);
  utt.lang=TTS_LANG_MAP[lang]||'en-IN';
  utt.rate=0.9;
  const voices=window.speechSynthesis.getVoices();
  const match=voices.find(v=>v.lang.startsWith(utt.lang.split('-')[0]));
  if(match) utt.voice=match;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utt);
}

// ── Photo ──────────────────────────────────────────────────────────────────
function handlePhoto(e){
  const file=e.target.files[0];
  if(!file) return;
  if(file.size>5*1024*1024){alert('Photo too large. Max 5 MB.');return;}
  const reader=new FileReader();
  reader.onload=ev=>{
    selectedImage={base64:ev.target.result,name:file.name};
    document.getElementById('previewThumb').src=ev.target.result;
    document.getElementById('previewName').textContent=file.name;
    imageStrip.classList.add('visible');
  };
  reader.readAsDataURL(file);
  e.target.value='';
}

function removeImage(){selectedImage=null;imageStrip.classList.remove('visible');document.getElementById('previewThumb').src='';}

// ── Voice Input ────────────────────────────────────────────────────────────
function toggleVoice(){
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){alert('Voice input works only in Chrome or Edge.');return;}
  isRecording?stopVoice():startVoice();
}

function startVoice(){
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  recognition=new SR();
  const lm={english:'en-IN',hindi:'hi-IN',marathi:'mr-IN',telugu:'te-IN',
             tamil:'ta-IN',kannada:'kn-IN',bengali:'bn-IN',gujarati:'gu-IN',punjabi:'pa-IN'};
  recognition.lang=lm[document.getElementById('languageSelect').value]||'en-IN';
  recognition.continuous=false; recognition.interimResults=false;
  recognition.onstart=()=>{isRecording=true;voiceBtn.classList.add('recording');voiceStatus.classList.add('visible');};
  recognition.onresult=e=>{chatInput.value=e.results[0][0].transcript;stopVoice();};
  recognition.onerror=e=>{stopVoice();if(e.error==='not-allowed')alert('Microphone permission denied.');};
  recognition.onend=()=>stopVoice();
  recognition.start();
}

function stopVoice(){isRecording=false;voiceBtn.classList.remove('recording');voiceStatus.classList.remove('visible');try{recognition&&recognition.stop();}catch(e){}}

// ── Send message ───────────────────────────────────────────────────────────
async function sendMessage(){
  const text=chatInput.value.trim();
  if(!text && !selectedImage) return;

  const imgToSend=selectedImage;
  const displayText=text||'📸 Please analyze this plant photo.';
  chatInput.value='';
  sendBtn.disabled=true;
  window.speechSynthesis&&window.speechSynthesis.cancel();

  appendMessage('user',displayText,imgToSend?imgToSend.base64:null,false);
  removeImage();
  appendMessage('bot','',null,true);

  try{
    const res=await fetch('/ask-expert',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        message:text||'Please analyze this plant image for any disease.',
        history:chatHistory,
        disease_context:document.getElementById('diseaseContext').value.trim(),
        language:document.getElementById('languageSelect').value,
        image_base64:imgToSend?imgToSend.base64:''
      })
    });
    const data=await res.json();
    document.getElementById('typing-indicator')?.remove();

    if(data.status==='success'){
      appendMessage('bot',data.reply,null,false);
      autoSpeak(data.reply);
      chatHistory.push({role:'user',content:displayText});
      chatHistory.push({role:'assistant',content:data.reply});
      if(chatHistory.length>20) chatHistory=chatHistory.slice(-20);
    } else {
      appendMessage('bot',`Sorry, I could not get a response.\n\nError: ${data.detail}\n\nYou can also call Kisan Helpline: 1800-180-1551`,null,false);
    }
  }catch(err){
    document.getElementById('typing-indicator')?.remove();
    appendMessage('bot','Network error. Please check your connection and try again.',null,false);
  }finally{sendBtn.disabled=false;chatInput.focus();}
}

// ── Save to Diary ──────────────────────────────────────────────────────────
async function saveSingleReply(replyText, btn){
  const msgs=chatHistory.slice(-4); // last 2 turns
  await _saveDiary(`AgriDoc Reply — ${new Date().toLocaleDateString()}`, msgs);
  btn.innerHTML='✅ Saved';
  btn.classList.add('saved');
  setTimeout(()=>{btn.innerHTML='📔 Save to Diary';btn.classList.remove('saved');},3000);
}

async function saveFullChat(){
  if(chatHistory.length===0){showToast('Nothing to save yet — have a conversation first!');return;}
  const title=`Farm Consultation — ${new Date().toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'})}`;
  await _saveDiary(title, chatHistory);
}

async function _saveDiary(title, messages){
  try{
    const lang=document.getElementById('languageSelect').value;
    const context=document.getElementById('diseaseContext').value.trim();
    const tags=['consultation'];
    if(context) tags.push(...context.split(',').map(s=>s.trim().split(':')[0].trim()).filter(Boolean).slice(0,3));

    const res=await fetch('/diary/save',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        type:'chat', title, language:lang,
        content:{messages, context_used:context},
        tags
      })
    });
    const d=await res.json();
    if(d.status==='success'){
      showToast('📔 Saved to your Farm Diary!');
    } else {
      showToast('Could not save: '+d.detail);
    }
  }catch(e){showToast('Network error while saving.');}
}

// ── Quick questions ────────────────────────────────────────────────────────
function sendQuick(btn){
  chatInput.value=btn.textContent.trim().replace(/^[^\w\s\u0900-\u097F]+\s*/u,'').trim();
  sendMessage();
}

// ── Clear chat ─────────────────────────────────────────────────────────────
function clearChat(){
  if(!confirm('Clear the chat?')) return;
  chatHistory=[]; removeImage();
  window.speechSynthesis&&window.speechSynthesis.cancel();
  chatMessages.innerHTML=`<div class="welcome-card"><div class="wi">🌾</div><h3>Namaste! I'm AgriDoc</h3><p>Chat cleared. Ask me anything — type, speak or upload a photo!</p></div>`;
}
</script>
</body>
</html>"""