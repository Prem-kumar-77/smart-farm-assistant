# Copilot Instructions for Smart Farm Assistant

## Project Overview
This project is a two-file demo for a smart farming assistant, consisting of a Streamlit frontend (`app.py`) and a FastAPI backend (`server.py`). The frontend interacts with the backend via HTTP requests to provide crop recommendations, weather tips, and plant disease remedies.

## Architecture
- **Frontend (`app.py`)**: Streamlit app with three main features. Communicates with backend using REST API calls to `http://127.0.0.1:8000`.
- **Backend (`server.py`)**: FastAPI server exposing three endpoints:
  - `POST /recommend_crop`: Returns a recommended crop based on soil type, rainfall, and season.
  - `GET /weather_tip`: Returns a daily weather tip based on the current weekday.
  - `GET /disease_help/{disease_name}`: Returns a remedy for a given plant disease.

## Developer Workflows
- **Run Backend**: Start FastAPI server (e.g., `uvicorn server:app --reload`).
- **Run Frontend**: Start Streamlit app (e.g., `streamlit run app.py`).
- **Testing**: No explicit test files; validate by running both apps and using the UI.
- **Debugging**: Use Streamlit and FastAPI error messages. Backend errors are returned as JSON with an `error` key.

## Project-Specific Patterns
- **Data Flow**: Frontend sends user input to backend, receives JSON responses, and displays results.
- **Error Handling**: Backend returns error messages in JSON; frontend displays them using Streamlit's `st.error`.
- **Conventions**:
  - Soil types: `loamy`, `clayey`, `sandy`, `laterite`
  - Diseases: `leaf_blight`, `powdery_mildew`, `root_rot`
  - Weather tips keyed by weekday
- **No database or persistent storage**; all data is in-memory dictionaries.

## Integration Points
- **External Dependencies**:
  - Frontend: `streamlit`, `requests`
  - Backend: `fastapi`, `pydantic`, `uvicorn` (for running)
- **Communication**: All frontend-backend communication is via HTTP on localhost.

## Examples
- Crop recommendation payload:
  ```json
  {"soil_type": "loamy", "rainfall_mm": 1200, "season": "monsoon"}
  ```
- Disease help endpoint:
  `GET /disease_help/leaf_blight`

## Key Files
- `app.py`: Streamlit UI and API calls
- `server.py`: FastAPI endpoints and logic

## Tips for AI Agents
- Always keep backend running before using frontend features.
- Follow the conventions for soil types and diseases to avoid errors.
- Update this file if new features, endpoints, or conventions are added.
