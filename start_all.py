import subprocess
import sys
import os
import time

project_dir = os.path.dirname(os.path.abspath(__file__))
venv_python = os.path.join(project_dir, "venv", "Scripts", "python.exe")

# Start Backend (FastAPI)
backend = subprocess.Popen([
    venv_python, "-m", "uvicorn", "Backend.server:app", "--reload", "--port", "8000"
], cwd=project_dir)

time.sleep(3)  # give backend time to start

# Start Frontend (Streamlit)
frontend = subprocess.Popen([
    venv_python, "-m", "streamlit", "run", os.path.join("Frontend", "app.py")
], cwd=project_dir)

print("✅ Backend running at http://127.0.0.1:8000")
print("✅ Frontend running at http://localhost:8501")

try:
    backend.wait()
    frontend.wait()
except KeyboardInterrupt:
    print("🛑 Shutting down...")
    backend.terminate()
    frontend.terminate()
