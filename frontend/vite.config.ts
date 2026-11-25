import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";

// In development the backend runs on :8000 and Vite proxies the API to it, so
// the page and the API share an origin (no CORS). The deployed build sets
// VITE_BACKEND_URL instead (step 7). MEDRA_DEV_BACKEND overrides the local
// target, e.g. when Windows reserves port 8000 (medra-serve --port 8765).
const backend = process.env.MEDRA_DEV_BACKEND ?? "http://127.0.0.1:8000";

export default defineConfig({
  base: "./",
  build: {
    // Two pages: the dashboard and the user study (estudio.html), which embeds it.
    rollupOptions: {
      input: {
        main: fileURLToPath(new URL("./index.html", import.meta.url)),
        estudio: fileURLToPath(new URL("./estudio.html", import.meta.url)),
      },
    },
  },
  server: {
    proxy: {
      "/sessions": { target: backend, ws: true },
      "/datasets": backend,
      "/sources": backend,
      "/health": backend,
      "/study": backend,
    },
  },
});
