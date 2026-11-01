import { defineConfig } from "vite";

// In development the backend runs on :8000 and Vite proxies the API to it, so
// the page and the API share an origin (no CORS). The deployed build sets
// VITE_BACKEND_URL instead (step 7).
const backend = "http://127.0.0.1:8000";

export default defineConfig({
  base: "./",
  server: {
    proxy: {
      "/sessions": { target: backend, ws: true },
      "/datasets": backend,
      "/sources": backend,
      "/health": backend,
    },
  },
});
