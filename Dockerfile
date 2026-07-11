# Backend de FISIAgent (FastAPI + BETO + RAG) — pensado para Hugging Face Spaces (SDK Docker).
# Build context: la raíz del repo (necesita FISIAgent-Back/ y BETO_model/).
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY FISIAgent-Back/requirements.txt ./requirements.txt

# PyTorch CPU-only primero: evita descargar la build con CUDA (varios GB de más,
# innecesarios porque los Spaces gratuitos no tienen GPU). El "torch" sin versión
# en requirements.txt queda satisfecho por esta instalación y no se reinstala.
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch \
 && pip install --no-cache-dir -r requirements.txt

COPY FISIAgent-Back/app ./app
COPY BETO_model /BETO_model

ENV BETO_MODEL_PATH=/BETO_model \
    PYTHONUNBUFFERED=1

# Hugging Face Spaces espera que el contenedor Docker escuche en el puerto 7860.
EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
