// Vitest 配置 — Invoice System v2.1
// 重点: jsdom 环境 + @vue/test-utils + 全局组件 mock (Vuetify/Pinia)
import { defineConfig } from "vitest/config";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  test: {
    globals: true,
    environment: "happy-dom",
    include: ["src/**/*.{test,spec}.{js,ts,vue}"],
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "lcov"],
      include: ["src/**/*.{js,vue}"],
      exclude: [
        "src/main.js",
        "src/router/**",
        "src/**/index.js",
        "src/**/*.test.js",
      ],
    },
  },
});
