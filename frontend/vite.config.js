import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ports = JSON.parse(
  readFileSync(join(__dirname, "..", "src", "backend", "config", "ports.json"), "utf-8"),
);
const { host, port } = ports.frontend;
const backendTarget = `http://${ports.backend.host}:${ports.backend.port}`;

/** Split large vendor bundles for faster first paint. */
function manualChunks(id) {
  if (!id.includes("node_modules")) return undefined;
  if (id.includes("element-plus")) return "element-plus";
  if (id.includes("@element-plus/icons-vue")) return "icons";
  if (id.includes("highlight.js")) return "highlight";
  if (id.includes("markdown-it")) return "markdown";
  if (id.includes("dompurify")) return "dompurify";
  if (id.includes("axios")) return "axios";
  if (id.includes("/vue/") || id.includes("/@vue/")) return "vue-vendor";
  return "vendor";
}

export default defineConfig({
  plugins: [vue()],
  server: {
    port,
    host,
    strictPort: true,
    proxy: {
      "/api": {
        target: backendTarget,
        changeOrigin: true,
      },
    },
  },
  build: {
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks,
      },
    },
  },
});
