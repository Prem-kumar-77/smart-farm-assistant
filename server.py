 # Backend/server.py  (cleaned, minimal changes)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import random
import datetime
import logging
import os
import cv2
import numpy as np
from fastapi import UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from .disease_model import predict_disease


# --- pest alerts import (try relative, then absolute, else fallback stub) ---
try:
    # when running as "Backend.server" this works
    from .modules.pest_alerts import fetch_rss_pest_news  # type: ignore
except Exception:
    try:
        # when running from project root (different import layout)
        from Backend.modules.pest_alerts import fetch_rss_pest_news  # type: ignore
    except Exception:
        # fallback stub to avoid server crash if import fails
        logging.warning("Could not import pest_alerts.fetch_rss_pest_news, using stub.")
        def fetch_rss_pest_news(region: str = "Kerala"):
            return []

# ---------------- APP ----------------
app = FastAPI(title="🌾 Smart Farming Assistant / സ്മാർട്ട് ഫാർമിംഗ് അസിസ്റ്റന്റ്")

# allow Streamlit (frontend) to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all during dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Reference images (for histogram matching) ----------------
# Use path relative to this file
REFERENCE_DIR = os.path.join(os.path.dirname(__file__), "reference_diseases")
# Build reference histograms only if folder exists
def compute_histogram_cv(img_rgb):
    # img_rgb: RGB numpy array HxWx3
    hist = cv2.calcHist([img_rgb], [0, 1, 2], None, [8, 8, 8], [0,256,0,256,0,256])
    cv2.normalize(hist, hist)
    return hist.flatten()

def read_image_cv(path):
    # Better robust read across platforms
    try:
        data = np.fromfile(path, dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if img is None:
            return None
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    except Exception:
        return None

def compare_histograms(h1, h2):
    # use correlation: higher = more similar (1.0 perfect)
    try:
        return float(cv2.compareHist(h1.astype('float32'), h2.astype('float32'), cv2.HISTCMP_CORREL))
    except Exception:
        return -1.0

ref_histograms = {}
if os.path.isdir(REFERENCE_DIR):
    for fname in os.listdir(REFERENCE_DIR):
        if fname.lower().endswith((".jpg", ".jpeg", ".png")):
            key = os.path.splitext(fname)[0].lower()
            img_rgb = read_image_cv(os.path.join(REFERENCE_DIR, fname))
            if img_rgb is None:
                continue
            ref_histograms[key] = compute_histogram_cv(img_rgb)
else:
    logging.warning(f"Reference images folder not found: {REFERENCE_DIR}")

# ---------------- CROPS DATASET ----------------
crops_data = {
    "loamy": ["Rice / അരി", "Banana / വാഴപ്പഴം", "Coconut / തേങ്ങ", "Maize / ചോളം",
              "Vegetables / പച്ചക്കറികൾ", "Papaya / കപ്പലണ്ടി", "Turmeric / മഞ്ഞൾ", "Ginger / ഇഞ്ചি"],
    "clayey": ["Paddy / നെല്ല്", "Sugarcane / കരിമ്പ്", "Wheat / ഗോതമ്പ്", "Cotton / പരുത്തി",
               "Jute / ചണ", "Gram / കടല", "Mustard / കടുക്", "Sesame / എള്ള്"],
    "sandy": ["Groundnut / നിലക്കടല", "Pineapple / കായപ്പഴം", "Watermelon / തണ്ണിമത്തൻ",
              "Millets / കുതിരവള്ളി", "Potato / ഉരുളക്കിഴങ്ങ്", "Sunflower / സൂർയകാന്തി"],
    "laterite": ["Rubber / റബ്ബർ", "Pepper / കുരുമുളക്", "Tea / ചായ", "Coffee / കാപ്പി",
                 "Cashew / കശുവണ്ടി", "Arecanut / അടയ്ക്ക", "Vanilla / വനില"],
    "black": ["Cotton / പരുത്തി", "Soybean / സോയാബീൻ", "Sorghum / ചോളം",
              "Sunflower / സോർയകാന്തി", "Tur / തുവരപ്പരിപ്പ്", "Castor / അവനക്കു"],
    "red": ["Groundnut / നിലക്കടല", "Millets / കുതിരവള്ളി", "Tobacco / പുകയില",
            "Onion / ഉള്ളി", "Tomato / തക്കാളി", "Chillies / മുളക്"],
    "alluvial": ["Rice / അരി", "Wheat / ഗോതമ്പ്", "Sugarcane / കരിമ്പ്", "Pulses / പരിപ്പ്",
                 "Oilseeds / എണ്ണ വിത്തുകൾ", "Potato / ഉരുളക്കിഴങ്ങ്", "Jute / ചണ"],
    "desert": ["Barley / വല്ലരി", "Millets / കുതിരവള്ളി", "Cumin / ജീരകം",
               "Mustard / കടുക്", "Guar / ഗ്വാർ"],
    "mountain": ["Apple / ആപ്പിൾ", "Tea / ചായ", "Barley / വല്ലരി",
                 "Maize / ചോളം", "Saffron / കുങ്കുമപ്പൂവ്", "Cardamom / ഏലം"]
}

# ---------------- DISEASE DATASET ----------------
disease_data = {
    "leaf_blight": "Spray copper fungicide; remove affected leaves. / ചെമ്പ് ഫംഗിസൈഡ് തളിക്കണം; ബാധിച്ച ഇലകൾ നീക്കം ചെയ്യണം.",
    "powdery_mildew": "Apply sulfur dust or neem oil weekly. / സൾഫർ പൊടി അല്ലെങ്കിൽ വേപ്പെണ്ണ ആഴ്ചതോറും തളിക്കുക.",
    "root_rot": "Improve drainage; fungicide drench required. / വെള്ളം നിൽക്കാതിരിക്കാൻ ശ്രദ്ധിക്കുക; ഫംഗിസൈഡ് ഒഴിക്കുക.",
    "bacterial_spot": "Use copper hydroxide spray; prune infected parts. / ചെമ്പ് ഹൈഡ്രോക്സൈഡ് തളിക്കുക; ബാധിച്ച ഭാഗങ്ങൾ മുറിക്കുക.",
    "rust": "Plant resistant varieties; spray triazole fungicides. / പ്രതിരോധ ഇനങ്ങൾ നട്ട് ട്രയാസോൾ ഫംഗിസൈഡ് തളിക്കുക.",
    "yellow_leaf_curl": "Control whiteflies with neem oil or insecticides. / വേപ്പെണ്ണയോ കീടനാശിനിയോ ഉപയോഗിച്ച് വെളുത്തപ്പറ്റ നിയന്ത്രിക്കുക.",
    "blast": "Use resistant seeds; carbendazim spray at 10-day intervals. / പ്രതിരോധ ശേഷിയുള്ള വിത്തുകൾ ഉപയോഗിക്കുക; 10 ദിവസത്തിലൊരിക്കൽ കാർബെൻഡാസിം തളിക്കുക.",
    "tikka_disease": "Spray chlorothalonil or mancozeb for 2–3 weeks. / 2–3 ആഴ്ചകൾക്കായി ക്ലോരോത്തലോണിൽ അല്ലെങ്കിൽ മാങ്കോസെബ് തളിക്കുക.",
    "wilt": "Rotate crops; soil solarization; fungicide treatment. / വിളകൾ മാറി കൃഷി ചെയ്യുക; മണ്ണ് സൂര്യപ്രകാശത്തിൽ വെക്കുക; ഫംഗിസൈഡ് ഉപയോഗിക്കുക.",
    "downy_mildew": "Spray metalaxyl + mancozeb; avoid overhead irrigation. / മെറ്റലാക്സിൽ + മాంకോസെബ് തളിക്കുക; മേൽനിന്നുള്ള ജലസേചനം ഒഴിവാക്കുക.",
    "anthracnose": "Remove infected fruits; spray carbendazim. / ബാധിച്ച പഴങ്ങൾ നീക്കംചെയ്യുക; കാർബെൻഡാസിം തളിക്കുക.",
    "early_blight": "Spray mancozeb or chlorothalonil at 7–10 day intervals. / മാങ്കോസെബ് അല്ലെങ്കിൽ ക്ലോരോത്തലോണിൽ 7–10 ദിവസത്തിലൊരിക്കൽ തളിക്കുക.",
    "late_blight": "Use metalaxyl + mancozeb spray, avoid excess irrigation. / മെറ്റലാക്സിൽ + മാങ്കോസെബ് തളിക്കുക, അധിക ജലസേചനം ഒഴിവാക്കുക.",
    "stem_borer": "Apply carbofuran granules at base; maintain field hygiene. / കാർബോഫുറാൻ ഗ്രാന്യൂൾ അടിയിൽ നൽകുക; വയൽ ശുചിത്വം പാലിക്കുക.",
    "fruit_rot": "Collect & destroy rotten fruits; apply fungicide sprays. / പുഴുതിന്ന പഴങ്ങൾ നീക്കംചെയ്ത് ഫംഗിസൈഡ് തളിക്കുക.",
    "sooty_mold": "Wash leaves with mild soap solution; control honeydew insects. / ഇലകൾ സോപ്പ് വെള്ളത്തിൽ കഴുകുക; പുഴുപ്പ് ഉൽപാദിപ്പിക്കുന്ന കീടങ്ങളെ നിയന്ത്രിക്കുക."
}

# ---------------- WEATHER TIPS ----------------
weather_tips = {
    "Monday": "Check soil moisture; plan irrigation if needed.",
    "Tuesday": "Apply organic manure or compost for soil health.",
    "Wednesday": "Inspect crops for pest/disease; early detection saves yield.",
    "Thursday": "Mulch to conserve water, reduce weeds, and enrich soil.",
    "Friday": "Prune diseased branches; spray preventive fungicides.",
    "Saturday": "Harvest mature crops; ensure safe storage facilities.",
    "Sunday": "Soil rest day; prepare crop rotation plan for next week."
}

# ---------------- FERTILIZER RULES ----------------
fertilizer_recommendations = {
    "rice": {"seedling": {"N": 80, "P": 40, "K": 40},
             "vegetative": {"N": 100, "P": 50, "K": 50},
             "flowering": {"N": 60, "P": 40, "K": 60}},
    "banana": {"seedling": {"N": 150, "P": 50, "K": 200},
               "vegetative": {"N": 200, "P": 60, "K": 250},
               "flowering": {"N": 100, "P": 40, "K": 150}},
    "coconut": {"seedling": {"N": 100, "P": 40, "K": 100},
                "vegetative": {"N": 200, "P": 50, "K": 250},
                "flowering": {"N": 150, "P": 60, "K": 200}},
    "groundnut": {"seedling": {"N": 40, "P": 60, "K": 40},
                  "vegetative": {"N": 50, "P": 70, "K": 50},
                  "flowering": {"N": 60, "P": 80, "K": 60}}
}

# ---------------- MODELS ----------------
class FarmerInput(BaseModel):
    soil_type: str
    rainfall_mm: float
    season: str

class FertilizerInput(BaseModel):
    crop: str
    stage: str
    soil_npk: Optional[dict] = {}

# ---------------- ENDPOINTS ----------------
@app.get("/")
def root():
    return {"status": "backend running"}

@app.post("/recommend_crop")
def recommend_crop(data: FarmerInput):
    soil = data.soil_type.lower()
    if soil in crops_data:
        return {"recommended_crop": random.choice(crops_data[soil])}
    return {"error": "Soil type not found."}

@app.get("/weather_tip")
def weather_tip():
    today = datetime.datetime.now().strftime("%A")
    return {"day": today, "tip": weather_tips.get(today, "No tip available.")}

# ---------------- REPLACE the /detect_disease endpoint with this implementation ----------------
@app.post("/detect_disease")
async def detect_disease(file: UploadFile = File(...)):
    """
    Robust image-based disease match using color-histogram comparison.
    Uses precomputed `ref_histograms` if available, else scans REFERENCE_DIR.
    Returns: { disease_detected, remedy, score } on success
             { error, score?, matched_key? } on failure
    """
    # validate
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    try:
        contents = await file.read()
        if not contents:
            return JSONResponse(status_code=400, content={"error": "Empty file uploaded."})
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Failed to read uploaded file: {e}"})

    # decode image from bytes robustly
    try:
        arr = np.frombuffer(contents, dtype=np.uint8)
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if bgr is None:
            return JSONResponse(status_code=400, content={"error": "Could not decode image. Unsupported or corrupted file."})
        upload_rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Error decoding image: {e}"})

    # compute histogram for uploaded image
    try:
        upload_hist = compute_histogram_cv(upload_rgb)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to compute histogram: {e}"})

    # search best match among reference histograms
    best_score = -1.0
    best_key = None

    # Try precomputed ref_histograms (constructed at startup) if present
    if isinstance(ref_histograms, dict) and ref_histograms:
        for key, ref_hist in ref_histograms.items():
            try:
                score = compare_histograms(upload_hist, ref_hist)
            except Exception:
                score = -1.0
            if score > best_score:
                best_score = score
                best_key = key
    else:
        # fallback: scan REFERENCE_DIR image files on demand
        if os.path.isdir(REFERENCE_DIR):
            for fname in os.listdir(REFERENCE_DIR):
                if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                key = os.path.splitext(fname)[0].lower()
                ref_img = read_image_cv(os.path.join(REFERENCE_DIR, fname))
                if ref_img is None:
                    continue
                try:
                    ref_hist = compute_histogram_cv(ref_img)
                    score = compare_histograms(upload_hist, ref_hist)
                except Exception:
                    score = -1.0
                if score > best_score:
                    best_score = score
                    best_key = key

    # threshold check - adjust 0.15 if too strict/lenient
    MIN_SCORE = 0.15
    if best_key is None or best_score < MIN_SCORE:
        return {"error": "No close disease match found.", "score": float(best_score)}

    # find remedy in the disease_data dictionary
    remedy = disease_data.get(best_key)
    if not remedy:
        # helpful response when a match was found but no remedy recorded
        return {
            "error": "Matched image found but remedy missing for key.",
            "matched_key": best_key,
            "score": float(best_score),
            "note": "Use /reference_list to inspect keys and /add_remedy to add remedy for this key."
        }

    # success
    return {"disease_detected": best_key, "remedy": remedy, "score": float(best_score)}

@app.post("/fertilizer_advice")
def fertilizer_advice(data: FertilizerInput):
    crop, stage = data.crop.lower(), data.stage.lower()
    if crop not in fertilizer_recommendations or stage not in fertilizer_recommendations[crop]:
        return {"error": "Crop/stage not found. / വിള/ഘട്ടം കണ്ടെത്താനായില്ല."}

    base_rec = fertilizer_recommendations[crop][stage].copy()
    soilN = data.soil_npk.get("N", 0)
    soilP = data.soil_npk.get("P", 0)
    soilK = data.soil_npk.get("K", 0)
    note = []

    # N logic
    if soilN > 250:
        base_rec["N"] = max(0, base_rec["N"] - 40)
        note.append("⚠️ Reduce Nitrogen; soil very high in N.")
    elif 200 < soilN <= 250:
        base_rec["N"] = max(0, base_rec["N"] - 30)
        note.append("⚠️ Reduce Nitrogen; soil already high in N.")
    elif soilN < 50:
        base_rec["N"] += 30
        note.append("⬆️ Increase Nitrogen; soil deficient.")
    elif 50 <= soilN < 100:
        base_rec["N"] += 15
        note.append("⬆️ Slightly increase Nitrogen.")

    # P logic
    if soilP > 120:
        base_rec["P"] = max(0, base_rec["P"] - 30)
        note.append("⚠️ Reduce Phosphorus; soil very high in P.")
    elif 100 < soilP <= 120:
        base_rec["P"] = max(0, base_rec["P"] - 20)
        note.append("⚠️ Reduce Phosphorus; soil already rich.")
    elif soilP < 20:
        base_rec["P"] += 20
        note.append("⬆️ Increase Phosphorus; soil deficient.")
    elif 20 <= soilP < 40:
        base_rec["P"] += 10
        note.append("⬆️ Slightly increase Phosphorus.")

    # K logic
    if soilK > 180:
        base_rec["K"] = max(0, base_rec["K"] - 35)
        note.append("⚠️ Reduce Potassium; soil very high in K.")
    elif 150 < soilK <= 180:
        base_rec["K"] = max(0, base_rec["K"] - 25)
        note.append("⚠️ Reduce Potassium; soil already high.")
    elif soilK < 40:
        base_rec["K"] += 25
        note.append("⬆️ Increase Potassium; soil deficient.")
    elif 40 <= soilK < 80:
        base_rec["K"] += 10
        note.append("⬆️ Slightly increase Potassium.")

    return {
        "recommended_NPK_kg_per_acre": base_rec,
        "note": " | ".join(note) if note else "✅ Balanced recommendation."
    }

@app.get("/pest_alerts")
def get_pest_alerts(region: str = "Kerala"):
    try:
        alerts = fetch_rss_pest_news(region)
        return {"alerts": alerts}
    except Exception as e:
        return {"error": str(e)}
