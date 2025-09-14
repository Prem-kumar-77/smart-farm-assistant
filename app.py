# app.py (Streamlit Frontend)
import streamlit as st
import requests

BACKEND_URL = "http://127.0.0.1:8000"

st.title("🌾 Smart Farming Assistant")

st.sidebar.title("Menu")
option = st.sidebar.radio("Choose Feature:", ["Crop Recommendation", "Weather Tip", "Disease Help"])

if option == "Crop Recommendation":
    st.header("🌱 Crop Recommendation")
    soil = st.selectbox("Choose soil type", ["loamy", "clayey", "sandy", "laterite"])
    rainfall = st.number_input("Enter rainfall (mm)", min_value=0, value=1200)
    season = st.selectbox("Choose season", ["monsoon", "summer", "winter"])

    if st.button("Get Crop Recommendation"):
        payload = {"soil_type": soil, "rainfall_mm": float(rainfall), "season": season}
        r = requests.post(f"{BACKEND_URL}/recommend_crop", json=payload)
        if r.status_code == 200:
            result = r.json()
            if "recommended_crop" in result:
                st.success(f"✅ Recommended Crop: {result['recommended_crop']}")
            else:
                st.error(result.get("error", "Unknown error"))

elif option == "Weather Tip":
    st.header("🌤️ Weather Tip of the Day")
    r = requests.get(f"{BACKEND_URL}/weather_tip")
    if r.status_code == 200:
        result = r.json()
        st.info(f"📅 {result['day']} Tip: {result['tip']}")

elif option == "Disease Help":
    st.header("🌿 Plant Disease Help")
    disease = st.selectbox("Choose disease", ["leaf_blight", "powdery_mildew", "root_rot"])
    if st.button("Get Remedy"):
        r = requests.get(f"{BACKEND_URL}/disease_help/{disease}")
        if r.status_code == 200:
            result = r.json()
            if "remedy" in result:
                st.warning(f"🩺 Remedy for {disease}: {result['remedy']}")
            else:
                st.error(result.get("error", "Unknown error"))
