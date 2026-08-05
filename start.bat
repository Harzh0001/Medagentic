@echo off
setlocal

REM ==== Critical fix: run from THIS file's folder, wherever the shell opened ====
cd /d "%~dp0"

if not exist venv (
    echo [setup] Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

if not exist .env (
    echo [setup] .env missing. Copying template...
    copy .env.example .env >nul
)

echo [setup] Installing dependencies (first run may take a minute)...
pip install -q -r requirements.txt

echo [run] Starting MedAgentic API on http://localhost:8000
echo [run] In a second terminal:  streamlit run ui\chat.py
uvicorn main:app --reload --port 8000
