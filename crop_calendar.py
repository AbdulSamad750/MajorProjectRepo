"""
crop_calendar.py — Crop Calendar Module for PlantDoc AI
Month-by-month farming guide for major Indian crops.
No database needed — fully static content.

Add to main.py:
    from crop_calendar import calendar_router
    app.include_router(calendar_router)
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

calendar_router = APIRouter()


@calendar_router.get("/crop-calendar")
async def crop_calendar_page():
    return HTMLResponse(content=_calendar_html())


def _calendar_html() -> str:
    return r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Crop Calendar – PlantDoc AI</title>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Merriweather:wght@400;700&display=swap" rel="stylesheet"/>
<style>
:root{
  --jan:#4a90d9; --feb:#6bb5e8; --mar:#f5a623; --apr:#e8724a;
  --may:#e85454; --jun:#3ab07a; --jul:#2d8a5e; --aug:#2d8a5e;
  --sep:#5a9e4f; --oct:#c8752a; --nov:#8b4513; --dec:#4a6fa5;
  --bg:#f0f7f0; --white:#ffffff; --dark:#1a2e1a; --mid:#4a6a4a;
  --light:#e8f5e3; --border:#c8dfc8;
}
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Nunito',sans-serif;background:var(--bg);color:var(--dark);min-height:100vh;}

/* Navbar */
.navbar{background:var(--dark);padding:.9rem 2rem;box-shadow:0 3px 15px rgba(0,0,0,.3);}
.nav-container{max-width:1300px;margin:0 auto;display:flex;justify-content:space-between;align-items:center;}
.logo{font-family:'Merriweather',serif;font-size:1.3rem;color:#a8d5a2;font-weight:700;}
.nav-links{display:flex;list-style:none;gap:1.5rem;}
.nav-links a{text-decoration:none;color:rgba(168,213,162,.75);font-size:.9rem;font-weight:600;padding:.35rem .8rem;border-radius:6px;transition:all .2s;}
.nav-links a:hover,.nav-links a.active{color:#a8d5a2;background:rgba(255,255,255,.1);}

/* Hero */
.hero{background:linear-gradient(135deg,var(--dark) 0%,#2d5a2d 50%,#4a8a3a 100%);
  padding:3rem 2rem 2.5rem;text-align:center;position:relative;overflow:hidden;}
.hero::after{content:'🌾🌿🌱🌻🍅🌽';font-size:3rem;position:absolute;bottom:-10px;left:50%;
  transform:translateX(-50%);opacity:.15;letter-spacing:1rem;white-space:nowrap;}
.hero h1{font-family:'Merriweather',serif;font-size:2.2rem;color:white;margin-bottom:.5rem;}
.hero p{color:rgba(255,255,255,.8);font-size:1.05rem;margin-bottom:1.5rem;}

/* Crop selector */
.crop-selector{display:flex;flex-wrap:wrap;justify-content:center;gap:.6rem;max-width:900px;margin:0 auto;}
.crop-chip{padding:.5rem 1.1rem;border-radius:25px;border:2px solid rgba(255,255,255,.3);
  background:rgba(255,255,255,.1);color:white;font-size:.88rem;font-weight:700;
  cursor:pointer;transition:all .25s;font-family:'Nunito',sans-serif;}
.crop-chip:hover{background:rgba(255,255,255,.2);border-color:rgba(255,255,255,.6);}
.crop-chip.active{background:white;color:var(--dark);border-color:white;box-shadow:0 4px 15px rgba(0,0,0,.2);}

/* Main content */
.main{max-width:1300px;margin:2rem auto;padding:0 1.5rem;}

/* Crop info banner */
.crop-banner{background:white;border-radius:14px;padding:1.5rem 2rem;margin-bottom:1.5rem;
  box-shadow:0 4px 20px rgba(0,0,0,.06);border:1px solid var(--border);
  display:flex;gap:2rem;align-items:center;flex-wrap:wrap;}
.crop-icon-big{font-size:4rem;flex-shrink:0;}
.crop-info-text h2{font-family:'Merriweather',serif;font-size:1.4rem;color:var(--dark);margin-bottom:.3rem;}
.crop-info-text p{color:var(--mid);font-size:.95rem;line-height:1.6;}
.crop-seasons{display:flex;gap:.6rem;margin-top:.6rem;flex-wrap:wrap;}
.season-tag{padding:.25rem .75rem;border-radius:12px;font-size:.8rem;font-weight:700;}
.season-kharif{background:#e8f5e3;color:#2d6a1a;}
.season-rabi{background:#e8f0ff;color:#3a4a9a;}
.season-zaid{background:#fff8e1;color:#9a6a00;}

/* Month grid */
.months-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:1.2rem;}

.month-card{background:white;border-radius:14px;overflow:hidden;
  box-shadow:0 4px 16px rgba(0,0,0,.06);border:1px solid var(--border);
  transition:transform .2s,box-shadow .2s;}
.month-card:hover{transform:translateY(-3px);box-shadow:0 8px 24px rgba(0,0,0,.1);}

.month-header{padding:.85rem 1.2rem;display:flex;justify-content:space-between;align-items:center;}
.month-name{font-size:1rem;font-weight:900;color:white;letter-spacing:.02em;}
.month-num{font-size:1.8rem;font-weight:900;color:rgba(255,255,255,.3);font-family:'Merriweather',serif;}

.month-body{padding:1rem 1.2rem;}

.activity-row{display:flex;gap:.6rem;margin-bottom:.6rem;align-items:flex-start;}
.activity-icon{font-size:1.1rem;flex-shrink:0;margin-top:.05rem;}
.activity-text{font-size:.88rem;color:#2a3a2a;line-height:1.5;}
.activity-text strong{color:var(--dark);}

.disease-alert{background:#fff4f4;border:1.5px solid #ffc8c8;border-radius:8px;
  padding:.6rem .9rem;margin-top:.8rem;font-size:.83rem;color:#8b2020;}
.disease-alert::before{content:'⚠️ Watch for: ';}

.tip-box{background:var(--light);border:1.5px solid var(--border);border-radius:8px;
  padding:.6rem .9rem;margin-top:.6rem;font-size:.83rem;color:var(--mid);}
.tip-box::before{content:'💡 Tip: ';}

/* Month colors applied via inline style in JS */

/* Legend */
.legend{display:flex;gap:1.5rem;flex-wrap:wrap;justify-content:center;margin:1.5rem 0;
  background:white;padding:1rem;border-radius:10px;border:1px solid var(--border);}
.legend-item{display:flex;align-items:center;gap:.4rem;font-size:.82rem;color:var(--mid);font-weight:600;}
.legend-dot{width:12px;height:12px;border-radius:50%;}
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
      <li><a href="/crop-calendar" class="active">Crop Calendar</a></li>
      <li><a href="/diary">My Diary</a></li>
    </ul>
  </div>
</nav>

<div class="hero">
  <h1>🌱 Crop Calendar</h1>
  <p>Month-by-month farming guide — what to do, when to spray, what disease to watch for</p>
  <div class="crop-selector" id="cropSelector"></div>
</div>

<div class="main">
  <div class="crop-banner" id="cropBanner"></div>
  <div class="legend">
    <div class="legend-item"><div class="legend-dot" style="background:#3ab07a"></div>Sowing / Planting</div>
    <div class="legend-item"><div class="legend-dot" style="background:#f5a623"></div>Fertilizing</div>
    <div class="legend-item"><div class="legend-dot" style="background:#4a90d9"></div>Irrigation</div>
    <div class="legend-item"><div class="legend-dot" style="background:#e85454"></div>Disease Watch</div>
    <div class="legend-item"><div class="legend-dot" style="background:#8b4513"></div>Harvesting</div>
  </div>
  <div class="months-grid" id="monthsGrid"></div>
</div>

<script>
const MONTH_COLORS = [
  '#4a90d9','#6bb5e8','#f5a623','#e8724a',
  '#e85454','#3ab07a','#2d8a5e','#2d8a5e',
  '#5a9e4f','#c8752a','#8b4513','#4a6fa5'
];
const MONTH_NAMES = ['January','February','March','April','May','June',
                     'July','August','September','October','November','December'];

const CROPS = {
  tomato:{
    name:'Tomato', icon:'🍅', season:['kharif','rabi'],
    desc:'Grown throughout India. Needs warm weather, well-drained soil. Highly susceptible to fungal and viral diseases.',
    calendar:[
      {sow:'Prepare nursery, sow seeds in trays',fert:'',irr:'Water nursery daily',disease:'Damping off in seedlings',tip:'Use cocopeat or sand in nursery mix'},
      {sow:'Transplant seedlings to main field',fert:'Apply basal dose of DAP',irr:'Water every 2-3 days',disease:'Early blight starting',tip:'Space plants 60cm apart for air circulation'},
      {sow:'',fert:'Apply urea top dressing',irr:'Irrigate at flowering stage',disease:'Powdery mildew risk increases',tip:'Apply neem oil spray as preventive'},
      {sow:'',fert:'Apply potassium fertilizer for fruit development',irr:'Regular irrigation critical at fruit set',disease:'Leaf curl virus — check for whiteflies',tip:'Use yellow sticky traps for whitefly control'},
      {sow:'',fert:'',irr:'Reduce irrigation as fruits ripen',disease:'Blossom end rot if water stress',tip:'Mulch soil to retain moisture'},
      {sow:'Summer crop transplanting',fert:'Apply organic compost',irr:'More frequent watering needed in heat',disease:'Fusarium wilt risk high',tip:'Avoid planting where tomato grew last year'},
      {sow:'',fert:'',irr:'Heavy irrigation needed',disease:'Bacterial wilt in waterlogged soil',tip:'Improve drainage before monsoon planting'},
      {sow:'Kharif nursery preparation',fert:'',irr:'Rain usually sufficient',disease:'Late blight — most dangerous season',tip:'Apply copper fungicide every 10 days during rain'},
      {sow:'Transplant kharif crop',fert:'Apply NPK 19:19:19',irr:'Supplement with irrigation if rains stop',disease:'Anthracnose on fruits',tip:'Harvest before full ripeness to reduce losses'},
      {sow:'',fert:'Final top dressing',irr:'Regular irrigation resumes',disease:'Yellow mosaic virus',tip:'Remove and destroy infected plants immediately'},
      {sow:'Rabi nursery preparation',fert:'Prepare field with manure',irr:'Irrigation every 4-5 days',disease:'Powdery mildew in cool weather',tip:'Ideal cool-weather growing season begins'},
      {sow:'Rabi transplanting',fert:'Apply DAP at transplanting',irr:'Water every 3 days',disease:'Early blight in cool damp weather',tip:'Best quality tomatoes grow in this cool season'}
    ]
  },
  soybean:{
    name:'Soybean', icon:'🫘', season:['kharif'],
    desc:'Major kharif oil seed crop in India. Grown in Madhya Pradesh, Maharashtra, Rajasthan. Needs 600-700mm rainfall.',
    calendar:[
      {sow:'',fert:'Prepare field, apply phosphorus',irr:'',disease:'',tip:'Test soil pH — soybean prefers 6.0-6.5'},
      {sow:'',fert:'Final field preparation',irr:'',disease:'',tip:'Treat seeds with Rhizobium culture to boost nitrogen'},
      {sow:'',fert:'',irr:'',disease:'',tip:'Procure certified seeds before season starts'},
      {sow:'',fert:'',irr:'',disease:'',tip:'Last chance to fix drainage issues in the field'},
      {sow:'',fert:'Apply basal dose DAP+MOP',irr:'',disease:'',tip:'Avoid sowing too early — wait for monsoon onset'},
      {sow:'Sowing begins (June 20 – July 10 ideal)',fert:'Seed treatment with fungicide + Rhizobium',irr:'Sow in moist soil',disease:'Stem rot if waterlogged',tip:'Sow at 5cm depth, 30cm row spacing'},
      {sow:'Main sowing period',fert:'',irr:'Rain generally sufficient',disease:'Yellow mosaic virus — watch for whiteflies',tip:'Keep field weed-free for first 30 days'},
      {sow:'',fert:'Apply urea if leaves are pale',irr:'Supplement if dry spell',disease:'Leaf crinkle disease',tip:'Spray profenofos for defoliating insects'},
      {sow:'',fert:'',irr:'Reduce irrigation at pod filling',disease:'Anthracnose on pods',tip:'Do not apply nitrogen now — it delays maturity'},
      {sow:'',fert:'',irr:'Stop irrigation 2 weeks before harvest',disease:'Charcoal rot in dry weather',tip:'Harvest when 95% leaves have dropped'},
      {sow:'',fert:'',irr:'',disease:'',tip:'Thresh immediately after harvest — do not delay'},
      {sow:'',fert:'',irr:'',disease:'',tip:'Store in dry, cool godown. Moisture below 12%'}
    ]
  },
  wheat:{
    name:'Wheat', icon:'🌾', season:['rabi'],
    desc:'Staple rabi crop across North India. Sown after monsoon in Oct-Nov, harvested in March-April. Needs cool weather.',
    calendar:[
      {sow:'',fert:'',irr:'',disease:'',tip:'Wheat harvested this month — clean and store threshed grain'},
      {sow:'',fert:'',irr:'',disease:'',tip:'After harvest, deep plow field to expose pests'},
      {sow:'',fert:'',irr:'',disease:'',tip:'Green manure crops can be sown now'},
      {sow:'',fert:'',irr:'',disease:'',tip:'Test soil, procure fertilizers early'},
      {sow:'',fert:'',irr:'',disease:'',tip:'Order certified wheat seeds — HD-2967, GW-322 varieties'},
      {sow:'',fert:'',irr:'',disease:'',tip:'Subsoil plowing in summer for pest control'},
      {sow:'',fert:'',irr:'',disease:'',tip:'Field should be free from previous crop residues'},
      {sow:'',fert:'',irr:'',disease:'',tip:'Prepare field bunds, check irrigation channels'},
      {sow:'',fert:'Apply farmyard manure and plow in',irr:'Pre-sowing irrigation (palewa)',disease:'',tip:'Ideal time to apply compost and lime if needed'},
      {sow:'Early sowing begins (Oct 15-25)',fert:'Apply full dose DAP at sowing',irr:'First irrigation at crown root stage (21 days)',disease:'Loose smut — use treated seed',tip:'Seed rate: 100 kg/acre for timely sowing'},
      {sow:'Main sowing window (Nov 1-20)',fert:'Apply urea at first irrigation',irr:'Irrigation at tillering stage',disease:'Yellow rust risk starts',tip:'Late sowing needs more seed — 125 kg/acre'},
      {sow:'',fert:'Apply second dose urea',irr:'Irrigation at jointing stage',disease:'Yellow rust, powdery mildew in cool damp weather',tip:'Spray propiconazole if rust spots appear'}
    ]
  },
  cotton:{
    name:'Cotton', icon:'🫧', season:['kharif'],
    desc:'Major cash crop in Gujarat, Maharashtra, Punjab. Requires long warm season (180-200 days). Very sensitive to diseases.',
    calendar:[
      {sow:'',fert:'',irr:'',disease:'',tip:'Plan varieties — Bt cotton hybrids recommended'},
      {sow:'',fert:'Deep plow field 30cm',irr:'',disease:'',tip:'Apply 10 tons FYM per acre in dry soil'},
      {sow:'',fert:'',irr:'Pre-sowing irrigation',disease:'',tip:'Last field prep before sowing season'},
      {sow:'',fert:'Apply DAP + MOP basal dose',irr:'',disease:'',tip:'Procure seeds — sow April-May in South India'},
      {sow:'Sowing in South India',fert:'',irr:'2-3 irrigations needed',disease:'Root rot in excess moisture',tip:'Maintain 90cm x 45cm spacing for Bt hybrids'},
      {sow:'Main sowing across India',fert:'Apply urea at squaring stage',irr:'Irrigation every 10-15 days',disease:'Thrips and aphids attack seedlings',tip:'Avoid excess nitrogen — causes vegetative growth'},
      {sow:'',fert:'Apply micronutrients (zinc, boron)',irr:'Critical at flowering',disease:'Leaf curl virus — monitor daily',tip:'Set up pheromone traps for bollworm'},
      {sow:'',fert:'Apply potash at boll development',irr:'Regular irrigation at boll development',disease:'Boll rot in humid conditions',tip:'Spray spinosad for bollworm control'},
      {sow:'',fert:'',irr:'Reduce irrigation as bolls open',disease:'Pink bollworm peak season',tip:'Harvest open bolls promptly to avoid quality loss'},
      {sow:'',fert:'',irr:'Stop irrigation 3 weeks before final harvest',disease:'Grey mildew in post-monsoon',tip:'Pick cotton in morning hours for best quality'},
      {sow:'',fert:'',irr:'',disease:'',tip:'Final picking — clear field, destroy crop residue'},
      {sow:'',fert:'',irr:'',disease:'',tip:'Deep plow after harvest to destroy soil pests'}
    ]
  },
  rice:{
    name:'Rice', icon:'🌾', season:['kharif','rabi'],
    desc:'Most important food crop in India. Grown in Eastern India, Kerala, Tamil Nadu. Needs flooded or waterlogged conditions.',
    calendar:[
      {sow:'',fert:'',irr:'',disease:'',tip:'Rabi rice harvest in some areas — dry and store carefully'},
      {sow:'',fert:'',irr:'',disease:'',tip:'Deep plow summer fallow to kill weeds and pests'},
      {sow:'',fert:'Apply green manure (Dhaincha)',irr:'',disease:'',tip:'Green manure adds 50-60 kg nitrogen/acre'},
      {sow:'',fert:'',irr:'',disease:'',tip:'Prepare nursery beds — sow 25 kg seed per acre nursery'},
      {sow:'Nursery sowing for early Kharif',fert:'',irr:'Water nursery daily',disease:'Damping off in nursery',tip:'Seed treatment with Carbendazim before sowing'},
      {sow:'Main nursery sowing',fert:'Apply basal DAP at transplanting',irr:'Maintain 5cm standing water',disease:'',tip:'Transplant 21-25 day old seedlings'},
      {sow:'Transplanting (July 1-15)',fert:'Apply urea at tillering',irr:'Maintain 5-7cm water depth',disease:'Leaf blast — watch in cloudy weather',tip:'Do not allow field to dry during tillering'},
      {sow:'',fert:'Apply second dose urea',irr:'Maintain water at panicle initiation',disease:'Neck blast — most critical stage',tip:'Spray tricyclazole at boot leaf stage as preventive'},
      {sow:'',fert:'Apply potash at grain filling',irr:'Irrigate until grain filling complete',disease:'Brown plant hopper — check weekly',tip:'Drain field 2 weeks before harvest for easy harvesting'},
      {sow:'',fert:'',irr:'Stop irrigation before harvest',disease:'Sheath blight in humid conditions',tip:'Harvest at 20-25% grain moisture'},
      {sow:'Rabi rice sowing in South',fert:'',irr:'',disease:'',tip:'Thresh and dry grain to below 14% moisture for storage'},
      {sow:'',fert:'',irr:'',disease:'',tip:'Keep stored rice in sealed bags away from moisture'}
    ]
  },
  chilli:{
    name:'Chilli', icon:'🌶️', season:['kharif','rabi'],
    desc:'Grown across Andhra Pradesh, Karnataka, Maharashtra. Highly profitable. Very susceptible to viral and fungal diseases.',
    calendar:[
      {sow:'',fert:'',irr:'',disease:'',tip:'Procure certified disease-free seeds'},
      {sow:'Rabi nursery sowing',fert:'',irr:'Water nursery regularly',disease:'Damping off risk',tip:'Sow in raised beds for better drainage'},
      {sow:'Rabi transplanting',fert:'Apply DAP basal',irr:'Every 5-7 days',disease:'Thrips attack on young plants',tip:'Apply neem oil at transplanting'},
      {sow:'',fert:'Apply urea top dressing',irr:'Regular irrigation',disease:'Powdery mildew risk',tip:'Mulching conserves moisture and reduces weeds'},
      {sow:'',fert:'Apply potassium at flowering',irr:'Critical irrigation at flowering',disease:'Anthracnose (fruit rot) starts',tip:'Remove and destroy diseased fruits immediately'},
      {sow:'Kharif nursery sowing',fert:'Apply FYM to nursery',irr:'',disease:'',tip:'First harvest of rabi crop this month'},
      {sow:'Kharif transplanting',fert:'Apply basal fertilizer',irr:'Rain supplemented',disease:'Leaf curl virus — peak season',tip:'Reflective mulch reduces whitefly attack'},
      {sow:'',fert:'',irr:'',disease:'Chilli mosaic virus',tip:'Remove and destroy infected plants — no cure'},
      {sow:'',fert:'Apply micronutrients (zinc+boron)',irr:'',disease:'Fruit rot in humid conditions',tip:'Apply copper fungicide during peak disease season'},
      {sow:'',fert:'',irr:'Reduce irrigation for drying',disease:'',tip:'Harvest red ripe chilli for drying'},
      {sow:'Rabi nursery starts again',fert:'',irr:'',disease:'',tip:'Dry harvested chilli in sun to below 8% moisture'},
      {sow:'',fert:'',irr:'',disease:'Powdery mildew in cool weather',tip:'Best growing season starts — cool weather ideal'}
    ]
  },
  maize:{
    name:'Maize', icon:'🌽', season:['kharif','rabi'],
    desc:'Third most important cereal crop. Grown in Karnataka, AP, MP, Bihar. Can be grown year-round in warm climates.',
    calendar:[
      {sow:'',fert:'',irr:'',disease:'',tip:'Rabi maize harvest — dry cobs before storage'},
      {sow:'',fert:'Deep plow and subsoil plow',irr:'',disease:'',tip:'Remove previous crop residues to reduce disease'},
      {sow:'Summer crop sowing possible',fert:'Apply FYM before sowing',irr:'Irrigation every 7 days in summer',disease:'',tip:'Short duration varieties for summer crop'},
      {sow:'',fert:'Apply urea at knee high stage',irr:'',disease:'Fall armyworm — major threat',tip:'Check crop daily for fall armyworm egg masses'},
      {sow:'',fert:'',irr:'',disease:'Fall armyworm peak',tip:'Spray Emamectin Benzoate for FAW control'},
      {sow:'Kharif sowing starts',fert:'Apply full basal dose',irr:'Rain usually sufficient',disease:'',tip:'Sow at 60x25cm spacing — 8 kg seed per acre'},
      {sow:'Main kharif planting',fert:'Apply urea at V6 stage',irr:'Supplement if dry spell',disease:'Turcicum leaf blight',tip:'Earth up plants at V6 stage to prevent lodging'},
      {sow:'',fert:'Apply second urea at tasseling',irr:'Critical at tasseling and silking',disease:'Downy mildew in humid conditions',tip:'Detassel if growing for seed production'},
      {sow:'',fert:'',irr:'Reduce irrigation at grain filling',disease:'Stalk rot',tip:'Harvest at 30% moisture, dry to 14% for storage'},
      {sow:'Rabi sowing begins',fert:'Apply basal dose for rabi',irr:'Irrigation every 10 days',disease:'',tip:'Best yields come from rabi maize in North India'},
      {sow:'',fert:'Apply urea at knee high',irr:'',disease:'',tip:'Rabi maize has less pest pressure — easier to grow'},
      {sow:'',fert:'',irr:'',disease:'',tip:'Harvest rabi crop before January heat'}
    ]
  },
  sugarcane:{
    name:'Sugarcane', icon:'🎋', season:['kharif'],
    desc:'Major cash crop in UP, Maharashtra, Karnataka. Long duration crop (12-18 months). High water requirement.',
    calendar:[
      {sow:'Spring planting (Jan-Mar is main season)',fert:'Apply FYM + phosphorus',irr:'Pre-planting irrigation',disease:'Red rot in stored setts',tip:'Use disease-free setts — treat with Carbendazim'},
      {sow:'Main spring planting',fert:'Apply full basal NPK',irr:'Every 8-10 days',disease:'',tip:'Plant 3-bud setts at 30cm depth'},
      {sow:'',fert:'Apply urea at 30 days',irr:'',disease:'Smut disease',tip:'Earth up furrows at 45 days'},
      {sow:'',fert:'Apply second dose urea',irr:'Every 7-10 days',disease:'Wilt in dry hot conditions',tip:'First propping to prevent lodging'},
      {sow:'',fert:'Apply potash for stalk development',irr:'Frequent irrigation in peak heat',disease:'Root rot if waterlogged',tip:'Remove dry leaves (trashing) from base'},
      {sow:'',fert:'',irr:'',disease:'Shoot borer active — check weekly',tip:'Apply Chlorpyrifos for shoot borer'},
      {sow:'',fert:'',irr:'Rain reduces irrigation need',disease:'Red rot in monsoon',tip:'Good drainage critical during monsoon'},
      {sow:'',fert:'Apply micronutrients',irr:'',disease:'Smut — remove infected plants',tip:'Stalk elongation phase — crop needs full sun'},
      {sow:'',fert:'',irr:'',disease:'',tip:'Avoid lodging — support with second propping'},
      {sow:'Autumn/adsali planting',fert:'',irr:'',disease:'',tip:'Maturity test — juice Brix should reach 18-20%'},
      {sow:'',fert:'',irr:'Reduce irrigation 30 days before harvest',disease:'',tip:'Harvest when top leaves dry and Brix is 18+'},
      {sow:'',fert:'',irr:'',disease:'',tip:'Ratoon management — apply fertilizer immediately after harvest'}
    ]
  }
};

let activeCrop = 'tomato';

function buildCropSelector() {
  const sel = document.getElementById('cropSelector');
  sel.innerHTML = Object.entries(CROPS).map(([key, c]) =>
    `<button class="crop-chip${key===activeCrop?' active':''}" onclick="selectCrop('${key}',this)">${c.icon} ${c.name}</button>`
  ).join('');
}

function selectCrop(key, btn) {
  activeCrop = key;
  document.querySelectorAll('.crop-chip').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderCrop();
}

function renderCrop() {
  const crop = CROPS[activeCrop];
  // Banner
  document.getElementById('cropBanner').innerHTML = `
    <div class="crop-icon-big">${crop.icon}</div>
    <div class="crop-info-text">
      <h2>${crop.name} Growing Guide</h2>
      <p>${crop.desc}</p>
      <div class="crop-seasons">
        ${crop.season.map(s => `<span class="season-tag season-${s}">${s.charAt(0).toUpperCase()+s.slice(1)} Season</span>`).join('')}
      </div>
    </div>`;

  // Month cards
  const today = new Date().getMonth(); // 0-based
  document.getElementById('monthsGrid').innerHTML = crop.calendar.map((m, i) => {
    const isNow = i === today;
    const activities = [];
    if (m.sow)     activities.push(`<div class="activity-row"><span class="activity-icon">🌱</span><div class="activity-text"><strong>Sow/Plant:</strong> ${m.sow}</div></div>`);
    if (m.fert)    activities.push(`<div class="activity-row"><span class="activity-icon">🧪</span><div class="activity-text"><strong>Fertilize:</strong> ${m.fert}</div></div>`);
    if (m.irr)     activities.push(`<div class="activity-row"><span class="activity-icon">💧</span><div class="activity-text"><strong>Water:</strong> ${m.irr}</div></div>`);
    if (!m.sow && !m.fert && !m.irr)
      activities.push(`<div class="activity-row"><span class="activity-icon">😴</span><div class="activity-text" style="color:#9a8a6a;font-style:italic;">Rest period for this crop</div></div>`);

    return `
      <div class="month-card" style="border-top:4px solid ${MONTH_COLORS[i]}${isNow?';box-shadow:0 0 0 3px '+MONTH_COLORS[i]+'44':''};${isNow?'transform:scale(1.02)':''}">
        <div class="month-header" style="background:${MONTH_COLORS[i]}">
          <div class="month-name">${isNow?'📍 ':''} ${MONTH_NAMES[i]}</div>
          <div class="month-num">${String(i+1).padStart(2,'0')}</div>
        </div>
        <div class="month-body">
          ${activities.join('')}
          ${m.disease ? `<div class="disease-alert">${m.disease}</div>` : ''}
          ${m.tip     ? `<div class="tip-box">${m.tip}</div>` : ''}
        </div>
      </div>`;
  }).join('');
}

buildCropSelector();
renderCrop();
// Smooth scroll to current month
setTimeout(() => {
  const cards = document.querySelectorAll('.month-card');
  const today = new Date().getMonth();
  if (cards[today]) cards[today].scrollIntoView({behavior:'smooth', block:'center'});
}, 400);
</script>
</body>
</html>"""