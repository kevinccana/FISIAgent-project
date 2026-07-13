FROM python:3.11-slim

# Instalamos git para descargar el modelo del Hub
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        git-lfs \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Descargamos el modelo directamente en el contenedor durante la construcción.
# El repo de modelo (kevinccana/FisiAgent-BETO) tiene los archivos anidados en
# una subcarpeta BETO_model/ (se subió una carpeta local que ya se llamaba así,
# en vez de subir su contenido a la raíz) -- de ahí el BETO_MODEL_PATH abajo.
RUN git lfs install && git clone https://huggingface.co/kevinccana/FisiAgent-BETO /app/beto-repo

COPY FISIAgent-Back/requirements.txt .

# Instalación de PyTorch CPU y dependencias
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch \
 && pip install --no-cache-dir -r requirements.txt

# Copiamos solo el código fuente
COPY FISIAgent-Back/app ./app

ENV BETO_MODEL_PATH=/app/beto-repo/BETO_model \
    PYTHONUNBUFFERED=1

EXPOSE 7860

# Render asigna su propio puerto en $PORT; Hugging Face Spaces y Docker local no
# lo setean, así que cae al 7860 de siempre. Forma "shell" del CMD para que la
# variable se expanda (la forma "exec" con corchetes no la expande).
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}