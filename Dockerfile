FROM python:3.11-slim

# Instalamos git para descargar el modelo del Hub
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        git-lfs \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Descargamos el modelo directamente en el contenedor durante la construcción
RUN git lfs install && git clone https://huggingface.co/kevinccana/FisiAgent-BETO /app/BETO_model

COPY FISIAgent-Back/requirements.txt .

# Instalación de PyTorch CPU y dependencias
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch \
 && pip install --no-cache-dir -r requirements.txt

# Copiamos solo el código fuente
COPY FISIAgent-Back/app ./app

ENV BETO_MODEL_PATH=/app/BETO_model \
    PYTHONUNBUFFERED=1

EXPOSE 7860

# Render asigna su propio puerto en $PORT; Hugging Face Spaces y Docker local no
# lo setean, así que cae al 7860 de siempre. Forma "shell" del CMD para que la
# variable se expanda (la forma "exec" con corchetes no la expande).
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}