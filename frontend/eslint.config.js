// ESLint v9 flat config — Invoice System v2.0
// Vue 3 + JavaScript (no TypeScript)
import js from "@eslint/js";
import pluginVue from "eslint-plugin-vue";

export default [
  // 基础 JS 推荐规则
  js.configs.recommended,

  // Vue 3 推荐规则
  ...pluginVue.configs["flat/recommended"],

  // 项目自定义规则
  {
    files: ["src/**/*.{js,vue}"],
    rules: {
      // ---------- 代码质量 ----------
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "no-debugger": "error",
      "no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
      "no-var": "error",
      "prefer-const": "error",

      // ---------- Vue 特定 ----------
      "vue/multi-word-component-names": "off", // 允许单词组件名（如 Dashboard、Settings）
      "vue/require-default-prop": "off",
      "vue/valid-v-slot": "off", // Vuetify 3 数据表格使用 #item.column 语法，ESLint 误判
      "vue/no-v-html": "off", // 搜索结果高亮需 v-html 渲染 <mark> 标签
      "vue/html-self-closing": ["warn", {
        html: { void: "always", normal: "never" },
      }],
      "vue/component-name-in-template-casing": ["error", "PascalCase"],
      "vue/attributes-order": ["warn", {
        order: ["DEFINITION", "LIST_RENDERING", "CONDITIONALS", "RENDER_MODIFIERS", "GLOBAL", "UNIQUE", "SLOT", "TWO_WAY_BINDING", "OTHER_DIRECTIVES", "OTHER_ATTR", "EVENTS", "CONTENT"],
      }],

      // ---------- 通用风格 ----------
      "no-multiple-empty-lines": ["warn", { max: 1 }],
      "comma-dangle": ["warn", "always-multiline"],
      "quotes": ["warn", "double", { avoidEscape: true }],
      "semi": ["warn", "always"],
    },
  },

  // 忽略目录
  {
    ignores: [
      "dist/**",
      "node_modules/**",
      "*.config.js",
    ],
  },
];
