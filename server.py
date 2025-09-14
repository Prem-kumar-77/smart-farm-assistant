# server.py (Backend API with multiple features)
from fastapi import FastAPI
from pydantic import BaseModel
import random
import datetime

app = FastAPI(title="🌾 Smart Farming Assistant")

# Crop recommendation dataset
crops_data = {
    "loamy": ["Rice", "Banana", "Coconut"],
    "clayey": ["Paddy", "Sugarcane"],
    "sandy": ["Groundnut", "Pineapple"],
    "laterite": ["Rubber", "Pepper", "Tea"]
}

# Remedies for demo disease detection
disease_data = {
    "leaf_blight": "Use copper-based fungicide spray weekly.",
    "powdery_mildew": "Apply sulfur dust to infected leaves.",
    "root_rot": "Improve drainage and avoid overwatering."
}

# Input model
class FarmerInput(BaseModel):
    soil_type: str
    rainfall_mm: float
    season: str

@app.post("/recommend_crop")
def recommend_crop(data: FarmerInput):
    soil = data.soil_type.lower()
    if soil in crops_data:
        crop = random.choice(crops_data[soil])
        return {"recommended_crop": crop, "soil": soil, "season": data.season}
    else:
        return {"error": "Soil type not found. Try loamy/clayey/sandy/laterite."}

@app.get("/weather_tip")
def weather_tip():
    today = datetime.datetime.now().strftime("%A")
    tips = {
        "Monday": "Check soil moisture before irrigation.",
        "Tuesday": "Apply organic manure if available.",
        "Wednesday": "Inspect crops for pest activity.",
        "Thursday": "Mulch to conserve soil moisture.",
        "Friday": "Prune diseased or dried leaves.",
        "Saturday": "Check market rates before harvesting.",
        "Sunday": "Let soil rest, no heavy farming today."
    }
    return {"day": today, "tip": tips[today]}

@app.get("/disease_help/{disease_name}")
def disease_help(disease_name: str):
    disease = disease_name.lower()
    if disease in disease_data:
        return {"disease": disease, "remedy": disease_data[disease]}
    else:
        return {"error": "Disease not found. Try leaf_blight, powdery_mildew, root_rot."}
