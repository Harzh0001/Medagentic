FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HUB_DISABLE_TELEMETRY=1

WORKDIR /app

# System deps for building wheels / running app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy project
COPY . .

# Download embedding model at build time to avoid cold-start latency
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Expose both backend and frontend ports
EXPOSE 8000 8501

# Start both FastAPI + Streamlit with a simple bash script
CMD ["bash", "-lc", "\
    uvicorn main:app --host 0.0.0.0 --port 8000 & \
    streamlit run ui/chat.py --server.port 8501 --server.address 0.0.0.0 --server.headless true \
  "]
