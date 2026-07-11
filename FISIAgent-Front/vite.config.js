import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ command }) => ({
  // GitHub Pages sirve el sitio en https://<usuario>.github.io/FISIAgent-project/,
  // así que el build de producción necesita ese subpath. `npm run dev` sigue en '/'.
  base: command === 'build' ? '/FISIAgent-project/' : '/',
  plugins: [react()],
}))
