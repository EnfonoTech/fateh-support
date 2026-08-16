import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "node:path";

export default defineConfig(({ command }) => ({
  plugins: [vue()],
  base: command === "serve" ? "/" : "/assets/fateh_support/frontend/",
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  build: {
    outDir: path.resolve(__dirname, "../fateh_support/public/frontend"),
    // NEVER set this to true. The entry is a stable `index.js` cache-busted by
    // a `?v=` query, so a browser (or the Capacitor WebView) can be holding an
    // entry from an earlier deploy that imports the chunk hashes of that build.
    // Wiping the directory deletes those chunks, the dynamic import 404s, and
    // every cached client hard-fails on boot until it happens to refetch the
    // entry. Old chunks are small; keeping them is the price of a stable entry
    // name. Prune deliberately, well after a deploy has settled.
    emptyOutDir: false,
    target: "es2020",
    cssCodeSplit: false,
    rollupOptions: {
      input: path.resolve(__dirname, "index.html"),
      output: {
        entryFileNames: "index.js",
        chunkFileNames: "chunks/[name]-[hash].js",
        assetFileNames: (info) => {
          if (info.name && info.name.endsWith(".css")) return "index.css";
          return "assets/[name]-[hash][extname]";
        },
      },
    },
  },
  server: {
    port: 8082,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: false },
      "/assets": { target: "http://localhost:8000", changeOrigin: false },
      "/fateh-sw.js": { target: "http://localhost:8000", changeOrigin: false },
      "/fateh-manifest.webmanifest": { target: "http://localhost:8000", changeOrigin: false },
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["tests/setup.ts"],
    globals: true,
  },
}));
