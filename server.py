 # server.py (expanded with pest_alerts + fertilizer_advice endpoints)
from fastapi import FastAPI
from pydantic import BaseModel
import random
import datetime

# Import voice modules
# Update these imports to match your actual directory structure or comment them out if the modules do not exist.
# For example, if 'tts.py' and 'SpeechRecognition.py' are in the same directory as server.py, use:
# from tts import router as tts_router
# from SpeechRecognition import router as stt_router

# Include voice module routers if available
# app.include_router(tts_router)
# app.include_router(stt_router)
app = FastAPI(title="🌾 Smart Farming Assistant / സ്മാർട്ട് ഫാർമിംഗ് അസിസ്റ്റന്റ്")

# Include voice module routers
app.include_router(tts_router)
app.include_router(stt_router)

# ---------------- CROPS DATASET ----------------
crops_data = {
    "loamy": ["Rice / അരി", "Banana / വാഴപ്പഴം", "Coconut / തേങ്ങ", "Maize / ചോളം", "Vegetables / പച്ചക്കറികൾ", "Papaya / കപ്പലണ്ടി", "Turmeric / മഞ്ഞൾ", "Ginger / ഇഞ്ചി"],
    "clayey": ["Paddy / നെല്ല്", "Sugarcane / കരിമ്പ്", "Wheat / ഗോതമ്പ്", "Cotton / പരുത്തി", "Jute / ചണ", "Gram / കടല", "Mustard / കടുക്", "Sesame / എള്ള്"],
    "sandy": ["Groundnut / നിലക്കടല", "Pineapple / കായപ്പഴം", "Watermelon / തണ്ണിമത്തൻ", "Millets / കുതിരവള്ളി", "Potato / ഉരുളക്കിഴങ്ങ്", "Sunflower / സൂർയകാന്തി"],
    "laterite": ["Rubber / റബ്ബർ", "Pepper / കുരുമുളക്", "Tea / ചായ", "Coffee / കാപ്പി", "Cashew / കശുവണ്ടി", "Arecanut / അടയ്ക്ക", "Vanilla / വനില"],
    "black": ["Cotton / പരുത്തി", "Soybean / സോയാബീൻ", "Sorghum / ചോളം", "Sunflower / സൂർയകാന്തി", "Tur / തുവരപ്പരിപ്പ്", "Castor / അവനക്കു"],
    "red": ["Groundnut / നിലക്കടല", "Millets / കുതിരവള്ളി", "Tobacco / പുകയില", "Onion / ഉള്ളി", "Tomato / തക്കാളി", "Chillies / മുളക്"],
    "alluvial": ["Rice / അരി", "Wheat / ഗോതമ്പ്", "Sugarcane / കരിമ്പ്", "Pulses / പരിപ്പ്", "Oilseeds / എണ്ണ വിത്തുകൾ", "Potato / ഉരുളക്കിഴങ്ങ്", "Jute / ചണ"],
    "desert": ["Barley / വല്ലരി", "Millets / കുതിരവള്ളി", "Cumin / ജീരകം", "Mustard / കടുക്", "Guar / ഗ്വാർ"],
    "mountain": ["Apple / ആപ്പിൾ", "Tea / ചായ", "Barley / വല്ലരി", "Maize / ചോളം", "Saffron / കുങ്കുമപ്പൂവ്", "Cardamom / ഏലം"]
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
    "downy_mildew": "Spray metalaxyl + mancozeb; avoid overhead irrigation. / മെറ്റലാക്സിൽ + മാങ്കോസെബ് തളിക്കുക; മേൽനിന്നുള്ള ജലസേചനം ഒഴിവാക്കുക.",
    "anthracnose": "Remove infected fruits; spray carbendazim. / ബാധിച്ച പഴങ്ങൾ നീക്കംചെയ്യുക; കാർബെൻഡാസിം തളിക്കുക."
}

# ---------------- WEATHER TIPS ----------------
tips = {
    "Monday": "Check soil moisture; plan irrigation if needed. / മണ്ണിലെ ഈർപ്പം പരിശോധിക്കുക; ആവശ്യമെങ്കിൽ ജലസേചനം ചെയ്യുക.",
    "Tuesday": "Apply organic manure or compost for soil health. / മണ്ണിന്റെ ആരോഗ്യം മെച്ചപ്പെടുത്താൻ ജൈവവളം അല്ലെങ്കിൽ കമ്പോസ്റ്റ് നൽകുക.",
    "Wednesday": "Inspect crops for pest/disease; early detection saves yield. / വിളയിൽ കീടരോഗങ്ങൾ പരിശോധിക്കുക; നേരത്തെ കണ്ടെത്തിയാൽ വിള രക്ഷിക്കാം.",
    "Thursday": "Mulch to conserve water, reduce weeds, and enrich soil. / വെള്ളം സംരക്ഷിക്കാൻ, പുല്ലുകൾ കുറയ്ക്കാൻ, മണ്ണ് സമ്പുഷ്ടമാക്കാൻ മുല്‍ച്ച് ചെയ്യുക.",
    "Friday": "Prune diseased branches; spray preventive fungicides. / രോഗബാധിതമായ കൊമ്പുകൾ വെട്ടി മാറ്റുക; പ്രതിരോധ ഫംഗിസൈഡ് തളിക്കുക.",
    "Saturday": "Harvest mature crops; ensure safe storage facilities. / വിളവെടുത്ത വിളകൾ സുരക്ഷിതമായി സംഭരിക്കുക.",
    "Sunday": "Soil rest day; prepare crop rotation plan for next week. / മണ്ണിന് വിശ്രമം നൽകുക; അടുത്ത ആഴ്ചയ്ക്ക് വിള പരിവർത്തന പദ്ധതി തയ്യാറാക്കുക."
}

# ---------------- PEST ALERTS ----------------
pest_alerts_data = [
    {"date": "2025-09-01", "pest": "Brown planthopper / തവിട്ടുപുഴു", "region": "Alappuzha"},
    {"date": "2025-09-03", "pest": "Bacterial wilt / ബാക്ടീരിയൽ വാട്ട്", "region": "Kozhikode"},
    {"date": "2025-09-05", "pest": "Fall armyworm / ഫാൾ ആർമിവോം", "region": "Thrissur"},
    {"date": "2025-09-07", "pest": "Fruit fly / പഴം ഈച്ച", "region": "Palakkad"},
]

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
    soil_npk: dict

# ---------------- ENDPOINTS ----------------
@app.post("/recommend_crop")
def recommend_crop(data: FarmerInput):
    soil = data.soil_type.lower()
    if soil in crops_data:
        crop = random.choice(crops_data[soil])
        return {"recommended_crop": crop}
    else:
        return {"error": "Soil type not found. / മണ്ണിന്റെ തരം കണ്ടെത്താനായില്ല."}

@app.get("/weather_tip")
def weather_tip():
    today = datetime.datetime.now().strftime("%A")
    return {"day": today, "tip": tips[today]}

@app.get("/disease_help/{disease_name}")
def disease_help(disease_name: str):
    disease = disease_name.lower()
    if disease in disease_data:
        return {"remedy": disease_data[disease]}
    else:
        return {"error": "Disease not found. / രോഗം കണ്ടെത്താനായില്ല."}

@app.get("/pest_alerts")
def pest_alerts(region: str = "Kerala"):
    alerts = [a for a in pest_alerts_data if region.lower() in a["region"].lower()]
    return alerts if alerts else []

@app.post("/fertilizer_advice")
def fertilizer_advice(data: FertilizerInput):
    crop = data.crop.lower()
    stage = data.stage.lower()
    soil_npk = data.soil_npk

    if crop in fertilizer_recommendations and stage in fertilizer_recommendations[crop]:
        rec = fertilizer_recommendations[crop][stage]
        note = ""
        if soil_npk.get("N", 0) > 200:
            note = "Reduce Nitrogen; soil already high in N. / നൈട്രജൻ കുറയ്ക്കുക; മണ്ണിൽ ഇതിനകം കൂടുതലുണ്ട്."
        return {
            "recommended_NPK_kg_per_acre": rec,
            "pesticide_note": note
        }
    else:
        return {"error": "Crop/stage not found. / വിള/ഘട്ടം കണ്ടെത്താനായില്ല."}
