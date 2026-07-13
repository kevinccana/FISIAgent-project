# Guía de despliegue — FISIAgent

Guía paso a paso para desplegar FISIAgent en la nube, gratis, usando:

- **Backend** (FastAPI + BETO + RAG) → [Render](https://render.com) (Web Service con Docker)
- **Frontend** (React + Vite) → [GitHub Pages](https://pages.github.com/)
- **CI/CD del frontend** → GitHub Actions (`.github/workflows/deploy-pages.yml`). El backend se despliega directo desde la integración nativa de Render con GitHub — no necesita un workflow propio.

No necesitas tarjeta de crédito para ninguno de los dos servicios.

> **Nota histórica:** este proyecto intentó primero desplegar el backend en Hugging Face Spaces. Se abandonó esa ruta porque el free tier de Spaces devolvía `Quota exceeded for flavor cpu-basic... limit=0` en dos cuentas distintas, sin ninguna verificación pendiente resoluble (ver el detalle en el historial de commits si hace falta retomarlo algún día). El modelo BETO sigue viviendo en `huggingface.co/kevinccana/FisiAgent-BETO` — eso no cambió, solo cambió dónde corre el contenedor.

---

## Índice

1. [Arquitectura del despliegue](#1-arquitectura-del-despliegue)
2. [Requisitos previos](#2-requisitos-previos)
3. [Paso 1 — Crear el Web Service en Render](#3-paso-1--crear-el-web-service-en-render)
4. [Paso 2 — Variables de entorno en Render](#4-paso-2--variables-de-entorno-en-render)
5. [Paso 3 — Configurar `VITE_API_URL` en GitHub](#5-paso-3--configurar-vite_api_url-en-github)
6. [Paso 4 — Habilitar GitHub Pages](#6-paso-4--habilitar-github-pages)
7. [Paso 5 — Verificar que todo funciona](#7-paso-5--verificar-que-todo-funciona)
8. [Probar la imagen Docker en tu máquina (opcional)](#8-probar-la-imagen-docker-en-tu-máquina-opcional)
9. [Actualizar el despliegue después del primero](#9-actualizar-el-despliegue-después-del-primero)
10. [Límites del tier gratuito y qué hacer si no alcanzan](#10-límites-del-tier-gratuito-y-qué-hacer-si-no-alcanzan)
11. [Troubleshooting — errores comunes y cómo resolverlos](#11-troubleshooting--errores-comunes-y-cómo-resolverlos)
12. [Cómo deshacer el despliegue](#12-cómo-deshacer-el-despliegue)

---

## 1. Arquitectura del despliegue

```
                              git push a main
                                    │
                    ┌───────────────┴───────────────┐
                    │                                │
                    ▼                                ▼
       Render (integración nativa       .github/workflows/deploy-pages.yml
        con GitHub, sin workflow)          (npm run build con VITE_API_URL)
                    │                                │
                    ▼                                ▼
            Render Web Service                 GitHub Pages
        (Docker, puerto vía $PORT)          (sitio estático)
        ┌──────────────────────┐           ┌──────────────────────┐
        │ FastAPI              │           │ React + Vite (dist/) │
        │ ├─ BETO (riesgo)     │  ◀─────── │ Llama a la API vía   │
        │ ├─ Gemini (chat)     │  fetch/   │ VITE_API_URL         │
        │ ├─ RAG (ChromaDB)    │  axios    │                      │
        │ └─ SQLite (mood/     │           │                      │
        │    tasks)            │           │                      │
        └──────────────────────┘           └──────────────────────┘
```

El backend se redespliega solo cuando Render detecta un push a `main` (lo vigila directo, sin pasar por Actions). El frontend sigue su propio workflow de GitHub Actions, independiente.

---

## 2. Requisitos previos

- El repositorio en GitHub con permisos de administrador (para Secrets, Variables y Pages).
- Una cuenta de [Render](https://dashboard.render.com/register) (gratis).
- Tu `GEMINI_API_KEY` de [Google AI Studio](https://aistudio.google.com/app/apikey).
- Que el repo ya tenga:
  - `Dockerfile` y `.dockerignore` en la raíz (el `Dockerfile` clona BETO desde `huggingface.co/kevinccana/FisiAgent-BETO` durante el build, y escucha en `${PORT:-7860}`)
  - `.github/workflows/deploy-pages.yml`
  - `vite.config.js` con `base: '/FISIAgent-project/'` en build
  - `api.js` leyendo `import.meta.env.VITE_API_URL`
  - `main.py` leyendo `FRONTEND_URL` para CORS

Verifica rápido que existen:

```bash
ls Dockerfile .dockerignore .github/workflows/deploy-pages.yml
```

---

## 3. Paso 1 — Crear el Web Service en Render

1. Entra a [dashboard.render.com](https://dashboard.render.com) → **New** → **Web Service**.
2. Conecta tu cuenta de GitHub si es la primera vez, y selecciona el repositorio `FISIAgent-project`.
3. Completa el formulario:
   - **Name**: por ejemplo `fisiagent-backend`.
   - **Region**: la más cercana a tus usuarios (no afecta el free tier).
   - **Branch**: `main`.
   - **Root Directory**: déjalo **vacío** (el `Dockerfile` ya usa rutas como `FISIAgent-Back/...` relativas a la raíz del repo).
   - **Runtime**: **Docker** (Render debería detectar el `Dockerfile` automáticamente).
   - **Instance Type**: **Free**.
4. Click **Create Web Service** — Render empieza el build de inmediato (tarda varios minutos la primera vez, ver sección 7).
5. Anota la URL que Render asigna, algo como `https://fisiagent-backend.onrender.com` (aparece arriba del dashboard del servicio en cuanto se crea, incluso antes de que termine de construir).

---

## 4. Paso 2 — Variables de entorno en Render

Dentro de tu Web Service → pestaña **Environment** → **Add Environment Variable**:

| Key | Value |
|-----|-------|
| `GEMINI_API_KEY` | Tu API key de Gemini |
| `FRONTEND_URL` | `https://tu-usuario.github.io` (sin la ruta del repo, sin `/` final — ver por qué en Troubleshooting) |
| `ENABLE_RAG` | `false` — **necesario en el free tier** (512MB RAM no alcanza para BETO + el modelo de embeddings de RAG a la vez, ver sección 10). Sin esta variable (o en local), RAG queda activo por defecto. |

Guarda los cambios — Render redespliega automáticamente el servicio cada vez que agregas o cambias una variable de entorno.

> `BETO_MODEL_PATH` no hace falta configurarla aquí — el `Dockerfile` ya la fija en `/app/BETO_model` (donde clona el modelo durante el build).

> **Con `ENABLE_RAG=false`:** el chat sigue funcionando completo (BETO clasificando riesgo + Gemini generando respuestas empáticas + protocolo de crisis), pero sin anclar las respuestas en los documentos de la FISI-UNSM — esa parte de la Funcionalidad 1 (RAG, Early Adopters) queda solo demostrada en el demo local, no en la versión pública.

### Sembrar datos de ejemplo (opcional, para que la demo no se vea vacía)

El free tier de Render no incluye una Shell dentro del contenedor, así que `seed_data.py` (que escribe directo al archivo SQLite) no se puede correr ahí. En su lugar, hay un endpoint HTTP que hace lo mismo:

1. Agrega la variable `SEED_TOKEN` en Environment (cualquier string que solo tú conozcas, ej. un password largo generado al azar). Sin esta variable, el endpoint responde 404 — no queda expuesto por accidente.
2. Con el servicio ya redesplegado, corre:
   ```bash
   curl -X POST https://tu-servicio.onrender.com/dev/seed-demo-data \
     -H "X-Seed-Token: el-mismo-valor-que-pusiste-en-SEED_TOKEN"
   ```
3. Respuesta esperada: `{"message": "Datos de ejemplo sembrados correctamente", "mood_entries": 30, "tasks": 17, ...}`.

Es idempotente — puedes correrlo varias veces, cada vez borra y vuelve a insertar los datos de `estudiante_demo` (el `USER_ID` que usa el frontend). Como el disco de Render es efímero, tendrás que volver a correrlo después de cada redeploy si quieres que la demo siga poblada.

---

## 5. Paso 3 — Configurar `VITE_API_URL` en GitHub

En el repo de GitHub: **Settings** → **Secrets and variables** → **Actions** → pestaña **Variables** → **New repository variable**.

| Name | Value |
|------|-------|
| `VITE_API_URL` | La URL de tu servicio de Render, ej. `https://fisiagent-backend.onrender.com` |

Esta variable la usa `deploy-pages.yml` al compilar el frontend — Vite la incrusta en el JS de producción, así que cualquier cambio a este valor requiere volver a correr ese workflow (ver paso 7).

---

## 6. Paso 4 — Habilitar GitHub Pages

1. En el repo de GitHub: **Settings** → **Pages**.
2. En **Build and deployment** → **Source**, selecciona **GitHub Actions** (no "Deploy from a branch").
3. No hace falta nada más aquí — el workflow `deploy-pages.yml` se encarga del resto la próxima vez que corra.

---

## 7. Paso 5 — Verificar que todo funciona

### Backend (Render)

1. En el dashboard de Render, espera a que el estado pase de "Deploying"/"Building" a **"Live"**.
2. Revisa la pestaña **Logs** — deberías ver la misma secuencia de `[Startup]` que en local:
   ```
   [Startup] ✓ BETO cargado correctamente
   [Startup] ✓ RAG inicializado correctamente
   [Startup] ✓ Sistema multi-agente inicializado (3 agentes + coordinador)
   [Startup] 🚀 FISIAgent listo
   ```
   Si en cambio el servicio se reinicia solo en bucle sin llegar a esas líneas, probablemente sea memoria insuficiente (ver Troubleshooting y sección 10).
3. Abre `https://tu-servicio.onrender.com/health` en el navegador — debería responder algo como `{"status": "ok"}`.

### Frontend (GitHub Pages)

1. Corre manualmente el workflow **"Deploy Frontend to GitHub Pages"** (Actions → seleccionarlo → Run workflow) para que tome el `VITE_API_URL` del paso 5.
2. Ve a **Settings → Pages** — ahí aparece la URL publicada, algo como `https://tu-usuario.github.io/FISIAgent-project/`.
3. Ábrela y prueba el chat, el registro de ánimo y el planificador. Abre las DevTools (F12) → pestaña **Network** y confirma que las peticiones van a tu URL de Render, no a `localhost`.
4. Si el chat no responde, abre la consola del navegador — un error de CORS ahí es la señal de que `FRONTEND_URL` no está bien configurado en Render (ver Troubleshooting).

---

## 8. Probar la imagen Docker en tu máquina (opcional)

Útil para depurar antes de esperar el build de Render:

```bash
# Desde la raíz del repo
docker build -t fisiagent-backend .

docker run -p 7860:7860 --env-file FISIAgent-Back/.env fisiagent-backend
```

Luego visita `http://localhost:7860/health`. El `Dockerfile` respeta la variable `$PORT` si está seteada (así es como funciona en Render) y usa `7860` como default si no (así corre local o en cualquier otro Docker plano).

Para iterar rápido sin reconstruir la imagen completa cada vez, puedes montar el código como volumen:

```bash
docker run -p 7860:7860 --env-file FISIAgent-Back/.env \
  -v "$(pwd)/FISIAgent-Back/app:/app/app" \
  fisiagent-backend
```

---

## 9. Actualizar el despliegue después del primero

- Cualquier `git push` a `main` que toque algo fuera de `FISIAgent-Front/` dispara un rebuild automático en Render (lo detecta directo, sin pasar por GitHub Actions).
- Cambios solo en `FISIAgent-Front/` → dispara `deploy-pages.yml` (por sus `paths:`), Render no hace nada porque no le tocó ningún archivo relevante.
- Si cambias una variable de entorno en Render (`GEMINI_API_KEY`, `FRONTEND_URL`), Render redespliega solo — no hace falta ningún paso extra.
- Si cambias `VITE_API_URL` en GitHub, sí necesitas volver a correr `deploy-pages.yml` manualmente (un cambio de Variable no dispara un run por sí solo).
- Para actualizar el modelo BETO: publica una nueva versión en `huggingface.co/kevinccana/FisiAgent-BETO` y fuerza un **Manual Deploy** en Render (dashboard del servicio → "Manual Deploy" → "Deploy latest commit") para que el `Dockerfile` lo vuelva a clonar.

---

## 10. Límites del tier gratuito y qué hacer si no alcanzan

| Recurso | Límite gratuito | Síntoma si se excede | Solución |
|---|---|---|---|
| RAM (Free instance) | 512 MB | `==> Out of memory (used over 512Mi)` en los logs, el servicio se reinicia en bucle sin llegar a "Startup complete" — truena cargando el modelo de embeddings de RAG, antes incluso de llegar a BETO | Ya resuelto con `ENABLE_RAG=false` (ver sección 4) — desactiva el modelo de embeddings de RAG, deja el chat funcionando con BETO + Gemini. Si aun así no alcanza, un plan de pago con más RAM |
| CPU (Free instance) | 0.1 vCPU compartida | Respuestas lentas, timeouts en la primera clasificación de BETO | Aceptable para demo/curso; plan de pago si se vuelve un problema real |
| Sleep por inactividad | El servicio se duerme tras ~15 min sin tráfico | La primera petición después de dormir tarda 30-60s (cold start) | Aceptable para un proyecto académico; un plan pago evita el sleep |
| Disco | Efímero (se borra en cada deploy) | `fisiagent.db` y `chroma_db/` vuelven a estar vacíos tras cada redeploy | Agregar un [Persistent Disk](https://render.com/docs/disks) de pago, o migrar a una base de datos externa gestionada |
| GitHub Pages | 1 GB de sitio, 100 GB/mes de ancho de banda | Muy improbable para una SPA de este tamaño | — |

---

## 11. Troubleshooting — errores comunes y cómo resolverlos

### El build falla o se cuelga durante `pip install`
- Causa típica: se está instalando la build de PyTorch con CUDA (varios GB) en vez de la CPU-only.
- Verifica que el `Dockerfile` tenga la línea `--index-url https://download.pytorch.org/whl/cpu` antes de instalar `torch`.

### El servicio se reinicia solo en bucle, nunca llega a "Live" / a los logs de `[Startup]`, o los logs dicen `Out of memory (used over 512Mi)`
- Causa confirmada: cargar `torch` + `transformers` + BETO **y** el modelo de embeddings de RAG (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) a la vez no entra en 512 MB — el crash pasa justo al construir `RAGAdapter`, antes de llegar a cargar BETO.
- Fix: agrega `ENABLE_RAG=false` en Environment (sección 4). El chat sigue funcionando (BETO + Gemini + protocolo de crisis), solo sin RAG.
- Si necesitas RAG también en producción, la alternativa es un plan de Render con más RAM (Starter o superior).

### En los logs aparece `[BETO] Carpeta del modelo no encontrada`
- El modelo se descarga durante el **build** del `Dockerfile` (`RUN git clone https://huggingface.co/kevinccana/FisiAgent-BETO /app/BETO_model`), no viaja versionado en este repo.
- Revisa los logs de **build** (no los de runtime) — un `git clone` fallido ahí es la causa más común (repo del modelo movido, hecho privado, o problema de red puntual — reintenta con "Manual Deploy").
- Confirma que `huggingface.co/kevinccana/FisiAgent-BETO` siga siendo público.

### Error de CORS en la consola del navegador (`blocked by CORS policy`)
- `FRONTEND_URL` no está configurado en Render, o no coincide exactamente con la URL de GitHub Pages.
- El header `Origin` que manda el navegador **nunca incluye la ruta** — así que el valor correcto es `https://tu-usuario.github.io`, **no** `https://tu-usuario.github.io/FISIAgent-project/`. `main.py` hace comparación exacta de string contra `allow_origins`.

### El frontend carga en blanco (pantalla vacía) en GitHub Pages
- Casi siempre es el `base` de `vite.config.js` mal configurado o el nombre del repo cambió.
- Verifica en `vite.config.js` que `base` coincida exactamente con `/NOMBRE-DEL-REPO/` (con las barras) tal como aparece en la URL de GitHub Pages.
- Revisa la consola del navegador: errores 404 en archivos `.js`/`.css` confirman este problema.

### El chat/planificador/mood muestran "No se pudo conectar con el backend"
- Verifica que `VITE_API_URL` esté bien configurada **antes** de que corriera el build de `deploy-pages.yml` (si la agregaste después, tienes que volver a correr el workflow manualmente).
- Verifica que el servicio de Render esté "Live" y no dormido — ábrelo directo en el navegador primero para despertarlo (cold start de 30-60s).

---

## 12. Cómo deshacer el despliegue

- **Pausar/borrar el servicio**: en Render, dashboard del servicio → Settings → "Suspend Web Service" (pausa sin borrar) o "Delete Web Service" (borra todo).
- **Deshabilitar GitHub Pages**: Settings del repo → Pages → Source → "Disable".
- **Detener el redeploy automático de Render sin borrar nada**: dashboard del servicio → Settings → "Auto-Deploy" → apágalo.
