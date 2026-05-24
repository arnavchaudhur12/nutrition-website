import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const frontendRoot = fileURLToPath(new URL(".", import.meta.url));
const sharedImagesRoot = fileURLToPath(new URL("../all_images", import.meta.url));

export default defineConfig({
  plugins: [react()],
  assetsInclude: ["**/*.PNG"],
  server: {
    port: 5173,
    fs: {
      allow: [frontendRoot, sharedImagesRoot]
    }
  }
});
