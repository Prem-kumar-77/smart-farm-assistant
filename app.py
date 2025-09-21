# Frontend/app.py
import streamlit as st
import requests
from PIL import Image
import os, io
import pandas as pd
import numpy as np

# ---------------- CONFIG ----------------
BACKEND_URL = "http://127.0.0.1:8000"
LOGO = "logo.png"
BANNER = "banner.jpg"
BG_IMAGE = "background.jpg"   # put your jpg in same folder

st.set_page_config(page_title="AI Farming Assistant", page_icon="🌱", layout="wide")

# ---------------- CSS ----------------
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

    .stApp {{ 
      background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), 
                  url("{BG_IMAGE}") no-repeat center center fixed; 
      background-size: cover; 
      color: #f0f6f5; 
      font-family: Inter, "Segoe UI", Roboto, Arial; 
    }}
    .card {{
        background: rgba(0, 0, 0, 0.55);
        border-radius: 15px;
        padding: 16px;
        margin-bottom: 16px;
    }}
    .title {{ font-size:28px; font-weight:700; color:#ecffef; margin-bottom:0px; font-family:'Poppins', sans-serif; }}
    .subtitle {{ font-size:14px; color:#c7d7ce; margin-top:2px; margin-bottom:8px; font-family:'Poppins', sans-serif; }}
    .muted {{ color:#b6c5bf; font-size:12px; font-family:'Poppins', sans-serif; }}
    .green {{ color:#9ef0b0; font-weight:600; font-family:'Poppins', sans-serif; }}
    .btn {{ background: linear-gradient(90deg,#2fa360,#1f8f46); color:#fff; border-radius:6px; padding:8px 12px; font-family:'Poppins', sans-serif; }}
    audio {{ width: 100% !important; margin-top: 10px; }}
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------- SIDEBAR ----------------
with st.sidebar:
    if os.path.exists(LOGO):
        st.image(LOGO, use_column_width=True)
    else:
        st.markdown("### 🌾 AI FARMING ASSISTANT")

    st.markdown("### 👩‍🌾 Farmer Profile")
    farmer_name = st.text_input("Name / പേര്", value="Agrifarm User")
    village = st.text_input("Village / ഗ്രാമം", value="Kerala")
    st.markdown("---")

    st.markdown("### 🧭 Menu / മെന്യൂ")
    menu = st.radio(
        "Choose a service / ഒരു സേവനം തിരഞ്ഞെടുക്കുക",
        (
            "Crop Recommendation / വിള നിർദ്ദേശം",
            "Weather Tip / കാലാവസ്ഥ ഉപദേശം",
            "Disease Help / രോഗസഹായം",
            "Fertilizer Advisor / വള നിർദേശം",
            "Pest Alerts / കീട മുന്നറിയിപ്പുകൾ",
            "Voice Assistant / ശബ്ദ സഹായി",
        ),
        label_visibility="collapsed",  # ✅ no warning
    )

    st.markdown("---")
    st.markdown("### ⚙️ Quick Actions")
    if st.button("📌 Save Profile"):
        st.success("Profile saved locally (demo).")

# ---------------- HEADER ----------------
if os.path.exists(BANNER):
    st.image(BANNER, use_container_width=True)

st.markdown("<div class='title'>🌾 AI Smart Farming Assistant — Kerala</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Localized crop advice, disease detection, weather & market tips.</div>", unsafe_allow_html=True)

# ---------------- Helper ----------------
def safe_request(method, path, json=None, files=None, timeout=10):
    try:
        url = BACKEND_URL.rstrip("/") + path
        if method == "POST":
            if files:
                return requests.post(url, files=files, timeout=timeout)
            return requests.post(url, json=json, timeout=timeout)
        else:  # GET
            return requests.get(url, params=json, timeout=timeout)
    except Exception as e:
        st.error(f"Network error: {e}")
        return None

# ---------------- MAIN CONTENT ----------------
left, right = st.columns([2.2, 1])

with left:
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    if menu.startswith("Crop Recommendation"):
        soil = st.selectbox("Choose soil type / മണ്ണ്", ["loamy","clayey","sandy","laterite","black","red","alluvial","desert","mountain"])
        rainfall = st.number_input("Rainfall (mm) / മഴ (mm)", min_value=0, value=1100)
        season = st.selectbox("Season / സീസൺ", ["monsoon","summer","winter"])
        if st.button("Get Crop Recommendation"):
            payload = {"soil_type": soil, "rainfall_mm": float(rainfall), "season": season}
            r = safe_request("POST", "/recommend_crop", json=payload)
            if r and r.status_code == 200:
                st.success(f"✅ Recommended Crop: {r.json().get('recommended_crop','Unknown')}")
            else:
                st.error("Failed to fetch crop recommendation.")

    elif menu.startswith("Weather Tip"):
        if st.button("Get Today's Tip"):
            r = safe_request("GET", "/weather_tip")
            if r and r.status_code == 200:
                st.success(r.json().get("tip","Tip not available"))
            else:
                st.error("Failed to fetch weather tip.")

    elif menu.startswith("Disease Help"):
        st.markdown("#### 🦠 Upload crop leaf image for disease detection")
        img_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

        if st.button("Analyze Disease") and img_file:
            files = {"file": (img_file.name, img_file.getvalue(), img_file.type)}
            # ✅ fixed endpoint name
            r = safe_request("POST", "/detect_disease", files=files)
            if r and r.status_code == 200:
                data = r.json()
                if "disease_detected" in data:
                    st.success(f"🧾 Disease: {data['disease_detected']}")
                    st.info(f"💡 Remedy: {data.get('remedy','No remedy found')}")
                elif "error" in data:
                    st.error(data["error"])
                else:
                    st.error("Unexpected response from backend.")
            else:
                st.error("Failed to analyze disease.")

    elif menu.startswith("Fertilizer Advisor"):
        crop = st.selectbox("Crop / വിള", ["rice","banana","coconut","groundnut"])
        stage = st.selectbox("Stage / ഘട്ടം", ["seedling","vegetative","flowering"])
        soil_n = st.number_input("Soil N (ppm)", min_value=0, value=100)
        soil_p = st.number_input("Soil P (ppm)", min_value=0, value=30)
        soil_k = st.number_input("Soil K (ppm)", min_value=0, value=80)
        if st.button("Get Fertilizer Advice"):
            payload = {"crop": crop, "stage": stage, "soil_npk": {"N": soil_n, "P": soil_p, "K": soil_k}}
            r = safe_request("POST", "/fertilizer_advice", json=payload)
            if r and r.status_code == 200:
                data = r.json()
                if "recommended_NPK_kg_per_acre" in data:
                    rec = data["recommended_NPK_kg_per_acre"]
                    st.success(f"Recommended N-P-K: N={rec['N']} • P={rec['P']} • K={rec['K']}")
                    if data.get("note"):
                        st.warning(data["note"])
                else:
                    st.error(data.get("error","Unknown error"))
            else:
                st.error("Failed to fetch fertilizer advice.")

    elif menu.startswith("Pest Alerts"):
        region = st.text_input("Region / പ്രദേശം", value=village)
        if st.button("Get Alerts"):
            r = safe_request("GET", "/pest_alerts", json={"region": region})
            if r and r.status_code == 200:
                try:
                    data = r.json()
                except Exception:
                    st.error("Backend returned invalid response.")
                    data = {}
                alerts = []
                if isinstance(data, dict) and "alerts" in data:
                    alerts = data["alerts"] or []
                elif isinstance(data, list):
                    alerts = data
                elif isinstance(data, dict) and "error" in data:
                    st.error(f"Backend error: {data['error']}")
                if not alerts:
                    st.info("No pest alerts found for your region.")
                else:
                    st.success(f"Found {len(alerts)} alert(s).")
                    for a in alerts:
                        title = a.get("title") or a.get("pest") or "Alert"
                        date = a.get("date") or ""
                        region_field = a.get("region") or region
                        link = a.get("link") or ""
                        with st.expander(f"{date} • {title[:100]}"):
                            st.write(f"**Region:** {region_field}")
                            if "source" in a:
                                st.write(f"**Source:** {a['source']}")
                            if link:
                                st.markdown(f"[Read more]({link})")
                            st.json(a)
            else:
                st.error("Failed to fetch pest alerts.")

    elif menu.startswith("Voice Assistant"):
        st.markdown("<div class='title'>🎙️ Voice Assistant</div>", unsafe_allow_html=True)
        audio = st.file_uploader("Upload voice (wav/mp3)", type=["wav","mp3"])
        if st.button("Ask with Voice") and audio:
            files = {"file": (audio.name, audio.getvalue(), audio.type)}
            r = safe_request("POST", "/voice_query", files=files, timeout=30)
            if r and r.status_code == 200:
                res = r.json()
                st.success(res.get("answer","No answer"))
                if "audio_reply" in res:
                    st.audio(res["audio_reply"], format="audio/wav")
            else:
                st.error("Failed to process voice query.")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- RIGHT PANEL ----------------
with right:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='title'>📈 Market Snapshot</div>", unsafe_allow_html=True)
    dates = pd.date_range(end=pd.Timestamp.today(), periods=7).strftime("%d-%b")
    df = pd.DataFrame({
        "Rice": np.random.randint(24, 33, size=7),
        "Banana": np.random.randint(16, 24, size=7),
        "Coconut": np.random.randint(18, 26, size=7),
    }, index=dates)
    st.line_chart(df)
    st.write(df.tail(1).T)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='title'>📎 Quick Links</div>", unsafe_allow_html=True)
    st.markdown("- Agmarknet prices\n- Krishi Bhavan contact\n- Subsidy links")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown("<div class='muted'>Powered by Smart Farming Assistant Backend</div>", unsafe_allow_html=True)
