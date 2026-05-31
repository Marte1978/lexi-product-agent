FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-descargar modelos (evita latencia al primer job)
RUN python -c "from livekit.plugins import silero; silero.VAD.load()" 2>/dev/null || true

COPY agent.py .
COPY .env .

CMD ["python", "agent.py", "start"]
