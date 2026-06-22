// 路由配置单元测试 — 重点: 404 fallback (P2 修复)
import { describe, it, expect } from "vitest";
import router from "../index";

describe("router", () => {
  it("定义了核心路由", () => {
    const paths = router.getRoutes().map((r) => r.path);
    expect(paths).toContain("/");
    expect(paths).toContain("/invoices");
    expect(paths).toContain("/settings");
  });

  it("包含向后兼容重定向", () => {
    const routes = router.getRoutes();
    const redirects = routes.filter((r) => r.redirect);
    expect(redirects.map((r) => r.path)).toEqual(
      expect.arrayContaining([
        "/upload",
        "/summary",
        "/categories",
        "/counterparts",
        "/reports",
      ]),
    );
  });

  it("有 404 fallback 路由 (P2 修复)", () => {
    // 关键回归测试: 访问不存在的路径应匹配 NotFound 路由
    const match = router.resolve("/this/path/does/not/exist");
    expect(match.name).toBe("NotFound");
  });

  it("404 路由解析到组件", () => {
    const match = router.resolve("/random/123");
    expect(match.matched.length).toBeGreaterThan(0);
    // component 是懒加载函数,执行后才是组件对象
    const matched = match.matched[0];
    expect(matched.components).toBeDefined();
  });

  it("向后兼容: /upload 路由存在并指向 /invoices/new", () => {
    // router.resolve 不展开重定向,直接检查 redirect 字段
    const route = router.getRoutes().find((r) => r.path === "/upload");
    expect(route).toBeDefined();
    expect(route.redirect).toBe("/invoices/new");
  });
});
