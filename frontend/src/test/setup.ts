import '@testing-library/jest-dom'

// Mock ResizeObserver (used by recharts ResponsiveContainer)
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverMock as any

// Mock URL.createObjectURL (used by maplibre-gl)
if (!globalThis.URL.createObjectURL) {
  globalThis.URL.createObjectURL = () => 'blob:mock'
}

// Mock fetch so pages don't fail on relative /api/* URLs in jsdom
globalThis.fetch = async () => ({
  ok: true,
  json: async () => ({}),
  text: async () => '',
}) as any
