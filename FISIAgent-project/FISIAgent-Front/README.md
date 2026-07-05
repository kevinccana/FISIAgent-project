# FISIAgent — Frontend

Interfaz de usuario de FISIAgent, construida con React 19 y Vite.

---

## Stack

- **React 19** — Framework UI con hooks
- **Vite 6** — Build tool con Hot Module Replacement
- **Axios** — Cliente HTTP para comunicación con el backend
- **CSS global** — Estilos sin framework externo (tema oscuro, variables CSS)

---

## Estructura

```
src/
├── pages/
│   ├── ChatPage.jsx         # Chat principal con IA
│   ├── MoodLogPage.jsx      # Registro de ánimo con calendario y gráficos SVG
│   ├── ResourcesPage.jsx    # Biblioteca de videos y recursos
│   └── SettingsPage.jsx     # Perfil y configuración
├── components/
│   ├── CrisisOverlay.jsx    # Modal de emergencia (nivel Crítico) — video + Línea 113
│   ├── VideoPopup.jsx       # Popup de video de apoyo (nivel Moderado)
│   └── Message.jsx          # Burbuja de mensaje individual
├── services/
│   └── api.js               # Llamadas al backend (sendMessage, checkHealth)
├── styles/
│   └── global.css           # Estilos globales y variables de color
└── assets/
    └── spritePics/          # Sprites PNG para los estados de ánimo
```

---

## Instalación

```bash
npm install
npm run dev
```

La app corre en `http://localhost:5173` y espera el backend en `http://localhost:8000`.

---

## Flujo del chat

1. El usuario escribe un mensaje en `ChatPage`.
2. `api.js` envía el historial completo al endpoint `/chatai` del backend.
3. El backend responde con la respuesta de Gemini + el nivel de riesgo detectado por BETO.
4. Según `nivel_riesgo`:
   - `"control"`  → se muestra solo la respuesta en el chat.
   - `"moderado"` → se muestra la respuesta + `VideoPopup` con un video de ayuda.
   - `"critico"`  → se muestra la respuesta + `CrisisOverlay` con números de emergencia.

---

## Variables de entorno

El frontend no requiere variables de entorno propias. La URL del backend está definida en [`src/services/api.js`](src/services/api.js):

```js
const API_URL = 'http://localhost:8000';
```

Cambiar esta línea si el backend está en otro host o puerto.

---

## Scripts disponibles

| Comando | Descripción |
|---------|-------------|
| `npm run dev` | Servidor de desarrollo con HMR |
| `npm run build` | Build de producción en `dist/` |
| `npm run preview` | Preview del build de producción |
| `npm run lint` | Linting con ESLint |
