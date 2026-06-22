// 测试 src/api/index.js 的 P2 修复点:
// 1) axiosLong 实例存在且 timeout = TIMEOUT_LONG (60s)
// 2) TIMEOUT_LONG > TIMEOUT_DEFAULT
// 3) 请求拦截器(请求/响应)正常挂载且不抛错
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

describe('src/api/index.js — P2 axiosLong + 拦截器', () => {
  let mod
  let apiModule

  beforeEach(async () => {
    // 清除 axios adapter 缓存,确保每次用最新 mock
    vi.restoreAllMocks()
    // 动态 import 以获取 fresh module
    mod = await import('@/api')
    apiModule = mod.default
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('P2-1: axiosLong 实例', () => {
    it('应导出 axiosLong 实例', () => {
      expect(mod.axiosLong).toBeDefined()
      expect(mod.axiosLong).toBeTruthy()
    })

    it('axiosLong 是 axios 实例(具备 axios 实例方法)', () => {
      expect(typeof mod.axiosLong.get).toBe('function')
      expect(typeof mod.axiosLong.post).toBe('function')
      expect(typeof mod.axiosLong.put).toBe('function')
      expect(typeof mod.axiosLong.delete).toBe('function')
      expect(typeof mod.axiosLong.interceptors).toBe('object')
    })

    it('axiosLong.defaults.timeout 应等于 TIMEOUT_LONG', () => {
      expect(mod.axiosLong.defaults.timeout).toBe(mod.TIMEOUT_LONG)
    })

    it('axiosLong.defaults.timeout 应等于 60000', () => {
      expect(mod.axiosLong.defaults.timeout).toBe(60000)
    })

    it('axiosLong.baseURL 应为 /api', () => {
      expect(mod.axiosLong.defaults.baseURL).toBe('/api')
    })

    it('axiosLong 与 api 默认实例是不同实例', () => {
      expect(mod.axiosLong).not.toBe(apiModule)
    })
  })

  describe('P2-2: TIMEOUT 常量', () => {
    it('应导出 TIMEOUT_DEFAULT', () => {
      expect(mod.TIMEOUT_DEFAULT).toBe(10000)
    })

    it('应导出 TIMEOUT_LONG', () => {
      expect(mod.TIMEOUT_LONG).toBe(60000)
    })

    it('TIMEOUT_LONG 应大于 TIMEOUT_DEFAULT', () => {
      expect(mod.TIMEOUT_LONG).toBeGreaterThan(mod.TIMEOUT_DEFAULT)
    })

    it('TIMEOUT_LONG 是 TIMEOUT_DEFAULT 的 6 倍', () => {
      // OCR 大文件识别需要比普通请求多 6 倍时间
      expect(mod.TIMEOUT_LONG / mod.TIMEOUT_DEFAULT).toBe(6)
    })
  })

  describe('P2-3: 默认 api 实例的拦截器挂载', () => {
    it('请求拦截器应至少挂载 1 个', () => {
      // interceptors.request.use 返回 interceptor id
      const handlers = apiModule.interceptors.request.handlers
      expect(handlers.length).toBeGreaterThanOrEqual(1)
    })

    it('响应拦截器应至少挂载 1 个', () => {
      const handlers = apiModule.interceptors.response.handlers
      expect(handlers.length).toBeGreaterThanOrEqual(1)
    })

    it('请求拦截器:fulfilled 必须是函数', () => {
      const handlers = apiModule.interceptors.request.handlers
      for (const h of handlers) {
        expect(typeof h.fulfilled).toBe('function')
      }
    })

    it('响应拦截器:fulfilled 必须是函数', () => {
      const handlers = apiModule.interceptors.response.handlers
      for (const h of handlers) {
        expect(typeof h.fulfilled).toBe('function')
      }
    })

    it('触发请求拦截器不应抛错(config 透传)', () => {
      const handlers = apiModule.interceptors.request.handlers
      const fakeConfig = { url: '/api/test', method: 'get', headers: {} }
      for (const h of handlers) {
        const result = h.fulfilled(fakeConfig)
        expect(result).toBeDefined()
        expect(result.url).toBe('/api/test')
      }
    })
  })

  describe('P2-3b: axiosLong 实例的拦截器挂载', () => {
    it('axiosLong 请求拦截器应至少挂载 1 个', () => {
      const handlers = mod.axiosLong.interceptors.request.handlers
      expect(handlers.length).toBeGreaterThanOrEqual(1)
    })

    it('axiosLong 响应拦截器应至少挂载 1 个', () => {
      const handlers = mod.axiosLong.interceptors.response.handlers
      expect(handlers.length).toBeGreaterThanOrEqual(1)
    })
  })

  describe('P2-3c: 触发请求不抛错(mock adapter)', () => {
    it('api.get 触发拦截器链不应抛错(请求配置被透传)', async () => {
      // 替换 adapter 为虚拟 adapter,避免真实网络请求
      apiModule.defaults.adapter = vi.fn(config =>
        Promise.resolve({
          data: { ok: true },
          status: 200,
          statusText: 'OK',
          headers: {},
          config,
          request: {}
        })
      )

      // 这里不 await 结果(响应拦截器会拆 .data,但 mock 已直接返回)
      // 关键是请求拦截器链不应抛错
      const promise = apiModule.get('/test')
      // 等待 microtask 跑完请求拦截器
      await expect(promise).resolves.toBeDefined()
    })

    it('axiosLong.get 触发拦截器链不应抛错', async () => {
      mod.axiosLong.defaults.adapter = vi.fn(config =>
        Promise.resolve({
          data: { ok: true },
          status: 200,
          statusText: 'OK',
          headers: {},
          config,
          request: {}
        })
      )

      const promise = mod.axiosLong.get('/ocr/recognize')
      await expect(promise).resolves.toBeDefined()
    })
  })
})