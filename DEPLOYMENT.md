# Guía de despliegue — FISIAgent

Guía paso a paso para desplegar FISIAgent en la nube, gratis, usando:

- **Backend** (FastAPI + BETO + RAG) → [Hugging Face Spaces](https://huggingface.co/spaces) (SDK Docker)
- **Frontend** (React + Vite) → [GitHub Pages](https://pages.github.com/)
- **CI/CD** → GitHub Actions (ya configurado en `.github/workflows/`)

No necesitas tarjeta de crédito para ninguno de los dos servicios.

---

## Índice

1. [Arquitectura del despliegue](#1-arquitectura-del-despliegue)
2. [Requisitos previos](#2-requisitos-previos)
3. [Paso 1 — Crear el Space en Hugging Face](#3-paso-1--crear-el-space-en-hugging-face)
4. [Paso 2 — Generar un token de acceso de Hugging Face](#4-paso-2--generar-un-token-de-acceso-de-hugging-face)
5. [Paso 3 — Configurar el `GEMINI_API_KEY` en el Space](#5-paso-3--configurar-el-gemini_api_key-en-el-space)
6. [Paso 4 — Configurar secrets y variables en GitHub](#6-paso-4--configurar-secrets-y-variables-en-github)
7. [Paso 5 — Habilitar GitHub Pages](#7-paso-5--habilitar-github-pages)
8. [Paso 6 — Disparar el primer despliegue](#8-paso-6--disparar-el-primer-despliegue)
9. [Paso 7 — Verificar que todo funciona](#9-paso-7--verificar-que-todo-funciona)
10. [Cómo funciona cada workflow (explicado)](#10-cómo-funciona-cada-workflow-explicado)
11. [Probar la imagen Docker en tu máquina (opcional)](#11-probar-la-imagen-docker-en-tu-máquina-opcional)
12. [Actualizar el despliegue después del primer push](#12-actualizar-el-despliegue-después-del-primer-push)
13. [Límites del tier gratuito y qué hacer si no alcanzan](#13-límites-del-tier-gratuito-y-qué-hacer-si-no-alcanzan)
14. [Troubleshooting — errores comunes y cómo resolverlos](#14-troubleshooting--errores-comunes-y-cómo-resolverlos)
15. [Cómo deshacer el despliegue](#15-cómo-deshacer-el-despliegue)

---

## 1. Arquitectura del despliegue

```
                              git push a main
                                    │
                    ┌───────────────┴───────────────┐
                    │                                │
                    ▼                                ▼
   .github/workflows/sync-to-hf.yml      .github/workflows/deploy-pages.yml
   (mirror del repo + Dockerfile raíz)    (npm run build con VITE_API_URL)
                    │                                │
                    ▼                                ▼
        Hugging Face Spaces                    GitHub Pages
        (SDK Docker, puerto 7860)          (sitio estático)
        ┌──────────────────────┐           ┌──────────────────────┐
        │ FastAPI              │           │ React + Vite (dist/) │
        │ ├─ BETO (riesgo)     │  ◀─────── │ Llama a la API vía   │
        │ ├─ Gemini (chat)     │  fetch/   │ VITE_API_URL         │
        │ ├─ RAG (ChromaDB)    │  axios    │                      │
        │ └─ SQLite (mood/     │           │                      │
        │    tasks)            │           │                      │
        └──────────────────────┘           └──────────────────────┘
```

Ambos despliegues son independientes: un cambio solo en `FISIAgent-Front/` no reconstruye el backend, y viceversa (ver los `paths:` de cada workflow).

---

## 2. Requisitos previos

- El repositorio en GitHub con permisos de administrador (para configurar Secrets, Variables y Pages).
- Una cuenta de [Hugging Face](https://huggingface.co/join) (gratis, sin tarjeta).
- Tu `GEMINI_API_KEY` de [Google AI Studio](https://aistudio.google.com/app/apikey).
- Que el repo ya tenga (si seguiste la sesión anterior, ya deberían existir):
  - `Dockerfile` y `.dockerignore` en la raíz
  - `.github/workflows/sync-to-hf.yml`
  - `.github/workflows/deploy-pages.yml`
  - `vite.config.js` con `base: '/FISIAgent-project/'` en build
  - `api.js` leyendo `import.meta.env.VITE_API_URL`
  - `main.py` leyendo `FRONTEND_URL` para CORS

Verifica rápido que existen:

```bash
ls Dockerfile .dockerignore .github/workflows/sync-to-hf.yml .github/workflows/deploy-pages.yml
```

---

## 3. Paso 1 — Crear el Space en Hugging Face

1. Inicia sesión en [huggingface.co](https://huggingface.co).
2. Click en tu avatar (arriba a la derecha) → **New Space**.
3. Completa el formulario:
   - **Owner**: tu usuario o una organización tuya.
   - **Space name**: por ejemplo `fisiagent-backend`.
   - **License**: la que prefieras (ej. `mit`), no afecta el despliegue.
   - **Select the Space SDK**: elige **Docker** → sub-opción **Blank** (plantilla en blanco; nuestro propio `Dockerfile` reemplazará el contenido).
   - **Space hardware**: deja el gratuito (`CPU basic · 2 vCPU · 16 GB RAM`).
   - **Visibility**: `Public` o `Private`, a tu criterio (si es privado, necesitarás autenticación para consumir la API desde el frontend público — para este proyecto se recomienda `Public`).
4. Click **Create Space**.
5. Anota el nombre completo que aparece en la URL: `https://huggingface.co/spaces/TU_USUARIO/fisiagent-backend`. La parte `TU_USUARIO/fisiagent-backend` es el valor que usarás como `HF_SPACE` más adelante.
6. El Space se crea con un Dockerfile de ejemplo — **no lo edites a mano**, el workflow de sync lo va a sobrescribir con el nuestro en el primer push. Puedes ignorar el mensaje de "Building" que aparece al crearlo.

---

## 4. Paso 2 — Generar un token de acceso de Hugging Face

1. Click en tu avatar → **Settings** → **Access Tokens** (o entra directo a [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)).
2. Click **Create new token**.
3. Tipo de token: **Write** (necesita permiso de escritura para que GitHub Actions pueda hacer `git push` al Space).
4. Nombre sugerido: `fisiagent-github-actions`.
5. Click **Generate a token** y **cópialo de inmediato** — Hugging Face no te lo vuelve a mostrar completo después.

> Guárdalo en un lugar seguro temporalmente (un gestor de contraseñas, o pégalo directo en el siguiente paso). Si lo pierdes, simplemente genera uno nuevo y repite el paso 6.

---

## 5. Paso 3 — Configurar el `GEMINI_API_KEY` en el Space

Este secret es **del Space**, no de GitHub — el contenedor lo lee directamente desde Hugging Face, no desde GitHub Actions.

1. Entra a la página de tu Space: `https://huggingface.co/spaces/TU_USUARIO/fisiagent-backend`.
2. Pestaña **Settings** (dentro del Space, no la de tu cuenta).
3. Sección **Variables and secrets** → **New secret**.
4. **Name**: `GEMINI_API_KEY`
   **Value**: tu API key de Gemini.
5. Guardar.

> Si más adelante quieres cambiar `BETO_MODEL_PATH` o cualquier otra variable, se configura igual en esta misma sección (como **Secret** si es sensible, o **Variable** si no lo es).

---

## 6. Paso 4 — Configurar secrets y variables en GitHub

En el repositorio de GitHub: **Settings** → **Secrets and variables** → **Actions**.

Hay dos pestañas: **Secrets** y **Variables**. Usa cada una según corresponda:

### Pestaña "Secrets" → "New repository secret"

| Name | Value |
|------|-------|
| `HF_TOKEN` | El token que generaste en el paso 4 (empieza con `hf_...`) |

### Pestaña "Variables" → "New repository variable"

| Name | Value | Ejemplo |
|------|-------|---------|
| `HF_SPACE` | `usuario/nombre-del-space` (sin la URL completa, sin `https://huggingface.co/spaces/`) | `jeison-cf/fisiagent-backend` |
| `VITE_API_URL` | La URL pública que Hugging Face asigna al Space | `https://jeison-cf-fisiagent-backend.hf.space` |

**¿Cómo se arma la URL pública del Space?** Hugging Face la genera reemplazando `/` por `-` y agregando `.hf.space`:

```
usuario/nombre-del-space  →  https://usuario-nombre-del-space.hf.space
```

Ejemplo: `jeison-cf/fisiagent-backend` → `https://jeison-cf-fisiagent-backend.hf.space`

> Puedes confirmar la URL exacta abriendo el Space en el navegador: aparece un botón "Embed this Space" / o simplemente visita la URL construida arriba una vez que el Space termine de construirse (paso 8) — si devuelve algo (aunque sea un error 404 de FastAPI antes de que termine de desplegar), la URL es correcta.

---

## 7. Paso 5 — Habilitar GitHub Pages

1. En el repo de GitHub: **Settings** → **Pages**.
2. En **Build and deployment** → **Source**, selecciona **GitHub Actions** (no "Deploy from a branch").
3. No hace falta nada más aquí — el workflow `deploy-pages.yml` se encarga del resto la próxima vez que corra.

---

## 8. Paso 6 — Disparar el primer despliegue

Con los 3 pasos anteriores (Space creado, secrets/variables en GitHub, Pages en modo Actions) ya puedes disparar el despliegue:

```bash
git add .
git commit -m "deploy: configurar despliegue en Hugging Face Spaces + GitHub Pages"
git push origin main
```

Esto dispara **ambos** workflows automáticamente (`sync-to-hf.yml` y `deploy-pages.yml`), porque ambos escuchan `push` a `main`.

Si prefieres dispararlos manualmente sin hacer un commit nuevo:

1. Pestaña **Actions** del repo.
2. Selecciona el workflow (`Sync Backend to Hugging Face Spaces` o `Deploy Frontend to GitHub Pages`) en la barra lateral izquierda.
3. Botón **Run workflow** → rama `main` → **Run workflow**.

### Qué esperar

- **`sync-to-hf.yml`** tarda poco (es solo un `git push` con Git LFS) — unos 1-3 minutos, más si es la primera vez que sube el modelo BETO (~420 MB) por LFS.
- Después de eso, **Hugging Face** empieza a construir la imagen Docker por su cuenta — esto lo ves en la pestaña **"Logs" → "Build logs"** del Space, no en GitHub Actions. La build tarda entre 5 y 15 minutos la primera vez (instala PyTorch, transformers, etc.). Los siguientes builds son más rápidos por el cache de capas de Docker.
- **`deploy-pages.yml`** tarda 1-2 minutos (build de Vite + publicación).

---

## 9. Paso 7 — Verificar que todo funciona

### Backend (Hugging Face Space)

1. Ve a `https://huggingface.co/spaces/TU_USUARIO/fisiagent-backend` y espera a que el estado pase de "Building" a **"Running"** (círculo verde).
2. Abre `https://TU_USUARIO-fisiagent-backend.hf.space/health` en el navegador — debería responder algo como `{"status": "ok"}`.
3. Abre `https://TU_USUARIO-fisiagent-backend.hf.space/` — debería devolver el JSON con `"status": "running"` que define `main.py`.
4. Revisa los **logs de la app** (pestaña "Logs" → "Container logs" del Space) y busca las líneas de `[Startup]` — deberías ver:
   ```
   [Startup] ✓ BETO cargado correctamente
   [Startup] ✓ RAG inicializado correctamente
   [Startup] ✓ Sistema multi-agente inicializado (3 agentes + coordinador)
   [Startup] 🚀 FISIAgent listo
   ```
   Si en cambio ves `[Startup] ⚠ BETO no disponible, usando fallback`, revisa la sección de Troubleshooting.

### Frontend (GitHub Pages)

1. Pestaña **Actions** → workflow `Deploy Frontend to GitHub Pages` → confirma que terminó en verde.
2. Ve a **Settings → Pages** — ahí aparece la URL publicada, algo como `https://tu-usuario.github.io/FISIAgent-project/`.
3. Ábrela y prueba el chat, el registro de ánimo y el planificador. Abre las DevTools (F12) → pestaña **Network** y confirma que las peticiones van a tu URL de Hugging Face (`VITE_API_URL`), no a `localhost`.
4. Si el chat no responde, abre la consola del navegador — un error de CORS ahí es la señal de que `FRONTEND_URL` no está bien configurado en el Space (ver Troubleshooting).

---

## 10. Cómo funciona cada workflow (explicado)

### `sync-to-hf.yml`

El modelo BETO **ya no viaja en este repo**: el `Dockerfile` lo clona directamente desde su propio repo de modelo en el Hub (`huggingface.co/kevinccana/FisiAgent-BETO`) durante el build del contenedor. Esto simplifica el workflow — ya no hace falta armar un subconjunto mínimo del repo, se puede mandar un mirror completo:

1. Hace `checkout` del repo completo, **incluyendo Git LFS** (`lfs: true`) — necesario para que los binarios trackeados con LFS a nivel raíz (`*.mp4`, `*.png`, `*.bin` — ver `.gitattributes`, ej. el video de `CrisisOverlay`) se traigan como archivos reales, no como punteros de texto.
2. Antepone temporalmente un bloque YAML (`sdk: docker`, `app_port: 7860`, etc.) al inicio de `README.md` **solo en el checkout local del runner** — Hugging Face necesita ese bloque para saber qué SDK usar y en qué puerto escuchar. Este cambio **no se sube a GitHub**, solo viaja hacia Hugging Face.
3. Hace un commit local (efímero, vive solo en el runner) con ese README modificado.
4. Hace `git lfs fetch --all` y agrega el repositorio del Space como remoto Git (`https://user:$HF_TOKEN@huggingface.co/spaces/$HF_SPACE`), luego `git push --force` — el `--force` es necesario porque el Space empieza con su propio historial de Git (el de la plantilla "Blank Docker") y no comparte ancestros con tu repo.
5. Al recibir el push, Hugging Face detecta el `Dockerfile` en la raíz y reconstruye automáticamente el contenedor — el paso `RUN git clone https://huggingface.co/kevinccana/FisiAgent-BETO /app/BETO_model` del `Dockerfile` descarga el modelo en ese momento.

> **Importante:** cualquier archivo binario grande que agregues al repo (frontend o backend) debe estar cubierto por un patrón en `.gitattributes` (`filter=lfs`) **y no debe estar en `.gitignore`** — ambas cosas a la vez impiden que `git add` lo trackee. Si un push a Hugging Face falla con *"Your push was rejected because it contains binary files"*, ese es el síntoma (ver Troubleshooting).

### `deploy-pages.yml`

1. Instala dependencias del frontend (`npm ci`) y compila con `npm run build`, inyectando `VITE_API_URL` como variable de entorno de build (Vite la incrusta en el JS compilado — por eso hay que configurarla en el paso 6 *antes* de este build).
2. Sube `FISIAgent-Front/dist/` como un "Pages artifact".
3. Un segundo job (`deploy`) publica ese artifact en GitHub Pages usando la acción oficial `actions/deploy-pages`.

---

## 11. Probar la imagen Docker en tu máquina (opcional)

Útil para depurar antes de esperar el build de Hugging Face:

```bash
# Desde la raíz del repo
docker build -t fisiagent-backend .

docker run -p 7860:7860 --env-file FISIAgent-Back/.env fisiagent-backend
```

Luego visita `http://localhost:7860/health`. Si esto funciona local pero falla en Hugging Face, el problema casi siempre es Git LFS (ver Troubleshooting) o memoria insuficiente.

Para iterar rápido sin reconstruir la imagen completa cada vez, puedes montar el código como volumen:

```bash
docker run -p 7860:7860 --env-file FISIAgent-Back/.env \
  -v "$(pwd)/FISIAgent-Back/app:/app/app" \
  fisiagent-backend
```

---

## 12. Actualizar el despliegue después del primer push

No hay que repetir nada de la configuración manual. Cualquier `git push` a `main` vuelve a disparar ambos workflows automáticamente:

- Cambios solo en `FISIAgent-Back/` o `Dockerfile` → solo corre `sync-to-hf.yml` (el workflow de Pages no tiene ningún `paths:` que matchee, así que no se dispara — revisa el archivo si agregas carpetas nuevas al backend). `BETO_model/` está gitignoreado, así que nunca genera un push por sí solo — para actualizar el modelo, publica una nueva versión en `huggingface.co/kevinccana/FisiAgent-BETO` y vuelve a correr `sync-to-hf.yml` manualmente para forzar un rebuild.
- Cambios solo en `FISIAgent-Front/` → solo corre `deploy-pages.yml`.
- Cambios en ambos → corren los dos, en paralelo.

Si cambias `VITE_API_URL` o `HF_SPACE` en GitHub (Settings → Secrets and variables → Actions), necesitas volver a correr el workflow correspondiente manualmente (botón "Run workflow") para que tome el nuevo valor — un cambio de Variable no dispara un run por sí solo.

---

## 13. Límites del tier gratuito y qué hacer si no alcanzan

| Recurso | Límite gratuito | Síntoma si se excede | Solución |
|---|---|---|---|
| RAM del Space (CPU basic) | 16 GB | Poco probable que falte para este proyecto; si el Space se reinicia solo, revisa los logs por "OOM" | Reduce el batch de RAG o usa un modelo BETO cuantizado |
| Disco del Space | Efímero (se borra en cada rebuild) | `fisiagent.db` y `chroma_db/` vuelven a estar vacíos después de cada push | Activar *Persistent Storage* (add-on de pago) en Settings del Space, o migrar a una base de datos externa gestionada |
| Sleep por inactividad | El Space se "duerme" tras un rato sin tráfico | La primera petición después de la inactividad tarda 10-30s (cold start) | Aceptable para un proyecto académico; si molesta, considera un plan de pago de Spaces ("Always On") |
| GitHub Pages | 1 GB de sitio, 100 GB/mes de ancho de banda | Muy improbable para una SPA de este tamaño | — |
| GitHub Actions (repos privados) | 2000 min/mes (gratis) — con GitHub Pro, más minutos incluidos | Workflows dejan de correr a mitad de mes | Repos públicos tienen minutos ilimitados en Actions |

---

## 14. Troubleshooting — errores comunes y cómo resolverlos

### El Space se queda en "Building" y falla con un error de memoria durante `pip install`
- Causa típica: se está instalando la build de PyTorch con CUDA (varios GB) en vez de la CPU-only.
- Verifica que el `Dockerfile` tenga la línea `--index-url https://download.pytorch.org/whl/cpu` antes de instalar `torch`.

### En los logs del Space aparece `[BETO] Carpeta del modelo no encontrada`
- El modelo se descarga durante el **build** del `Dockerfile` (`RUN git clone https://huggingface.co/kevinccana/FisiAgent-BETO /app/BETO_model`), no viaja versionado en este repo. Si esto falla:
  - Revisa los **Build logs** del Space (no los Container logs) — un `git clone` fallido ahí es la causa más común (repo del modelo movido, hecho privado, o rate-limit).
  - Confirma que `huggingface.co/kevinccana/FisiAgent-BETO` sea público (o que el Space tenga credenciales para clonarlo si es privado).
  - Verifica que `BETO_MODEL_PATH=/app/BETO_model` (seteado en el `Dockerfile`) coincida con el destino del `git clone`.

### `remote: Your push was rejected because it contains binary files` (menciona un `.mp4`, `.png` u otro binario)
- Causa: ese archivo no está cubierto por un patrón `filter=lfs` en algún `.gitattributes` del repo, **o** está listado en `.gitignore` (lo que bloquea que `git add` lo trackee, incluso si `.gitattributes` sí lo cubre — ambos archivos actúan en conjunto).
- Fix: agrega el patrón correspondiente a `.gitattributes` (raíz del repo, ej. `*.mp4 filter=lfs diff=lfs merge=lfs -text`) y confirma que **no** haya una entrada que lo ignore en `.gitignore`. Luego vuelve a agregar el archivo (`git rm --cached <archivo>` seguido de `git add <archivo>` si ya estaba trackeado sin LFS) para que el filtro LFS lo re-procese.

### Error de CORS en la consola del navegador (`blocked by CORS policy`)
- `FRONTEND_URL` no está configurado en el backend, o no coincide exactamente con la URL de GitHub Pages (protocolo `https://`, sin `/` final).
- Solución: agrega la variable **`FRONTEND_URL`** como *Variable* (no Secret) en el Space de Hugging Face — recuerda que este es un env var que lee `main.py`, así que también puede vivir en el propio Space, igual que `GEMINI_API_KEY` (paso 5).
- Ejemplo de valor: `https://tu-usuario.github.io`

### El frontend carga en blanco (pantalla vacía) en GitHub Pages
- Casi siempre es el `base` de `vite.config.js` mal configurado o el nombre del repo cambió.
- Verifica en `vite.config.js` que `base` coincida exactamente con `/NOMBRE-DEL-REPO/` (con las barras) tal como aparece en la URL de GitHub Pages.
- Revisa la consola del navegador: errores 404 en archivos `.js`/`.css` confirman este problema.

### El chat/planificador/mood muestran "No se pudo conectar con el backend"
- Verifica que `VITE_API_URL` esté bien configurada **antes** de que corriera el build de `deploy-pages.yml` (si la agregaste después, tienes que volver a correr el workflow manualmente).
- Verifica que el Space esté "Running" y no dormido — ábrelo directo en el navegador primero para despertarlo.

### `git push --force hf HEAD:main` falla con "Permission denied" o 401
- El `HF_TOKEN` expiró, se generó como `Read` en vez de `Write`, o el secret en GitHub no se llama exactamente `HF_TOKEN`.
- Genera un nuevo token con permiso **Write** (paso 4) y actualiza el secret en GitHub.

---

## 15. Cómo deshacer el despliegue

- **Pausar/borrar el Space**: en Hugging Face, Settings del Space → "Pause Space" (detiene sin borrar) o "Delete this Space" (borra todo).
- **Deshabilitar GitHub Pages**: Settings del repo → Pages → Source → "Disable".
- **Detener los workflows sin borrar nada**: renombra o borra los archivos `.github/workflows/sync-to-hf.yml` y `.github/workflows/deploy-pages.yml` (o coméntales el trigger `push`).
