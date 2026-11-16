import { defineConfig } from "astro/config";
import {vkNewsPreview} from './scripts/vk-news-dev.mjs';
import production from './deploy/production.json' with {type:'json'};

export default defineConfig({
  site: process.env.SOYUZ_RELEASE==='1'?production.origin:undefined,
  output: "static",
  trailingSlash: "always",
  devToolbar: { enabled: false },
  vite: {
    plugins:[vkNewsPreview()],
    server: {
      watch: {
        // The workspace drive does not reliably deliver native change events.
        usePolling: true,
        interval: 250,
        binaryInterval: 1000,
        ignored: ["**/tmp/**", "**/archive/**", "**/.local/**", "**/dist/**", "**/games/**"],
      },
    },
  },
});
