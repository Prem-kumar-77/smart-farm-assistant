# 🌱 AI-Powered Personal Farming Assistant for Kerala

Smart India Hackathon 2025 | Team Formula 1  

## 🚜 Problem
- Farmers struggle with accurate crop planning and decisions  
- Lack of localized pest and disease prediction tools  
- Limited access to real-time market and weather insights  

## 💡 Solution
An AI-driven bilingual farming assistant that provides:  
- Crop recommendations using soil, season, and rainfall  
- Image-based plant disease detection with deep learning (ONNX)  
- Fertilizer and irrigation optimization advisory  
- Automated pest alerts from trusted news feeds  
- Real-time market price intelligence (Agmarknet)  
- Malayalam + English voice/text interface  

## 🛠 Tech Stack
- **Backend**: FastAPI (Python)  
- **Frontend**: Streamlit (Python)  
- **ML Models**: ONNX (deep learning)  
- **Hosting**: Render / Streamlit Cloud  
- **Languages**: Python, Malayalam + English support  

## 📦 Installation (Run Locally)
```bash
# Clone the repo
git clone https://github.com/Prem-kumar-77/smart-farm-assistant.git
cd smart-farm-assistant

# Install dependencies
pip install -r requirements.txt

# (Optional) Download models
python download_models.py

# Run backend (FastAPI)
uvicorn main:app --reload

# Run frontend (Streamlit)
streamlit run streamlit_app.py
