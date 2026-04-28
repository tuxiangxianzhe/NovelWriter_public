import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// ── 响应拦截器：统一错误处理 ──────────────────────────────────────────────────
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const raw = err.response?.data?.detail ?? err.message ?? '请求失败'
    const msg = Array.isArray(raw) ? raw.map((e: any) => e.msg ?? JSON.stringify(e)).join('; ') : String(raw)
    return Promise.reject(new Error(msg))
  }
)

// ── Projects ─────────────────────────────────────────────────────────────────
export const projectsApi = {
  list: () => api.get('/projects'),
  create: (name: string, filepath = '') => api.post('/projects', { name, filepath }),
  activate: (name: string) => api.post(`/projects/${encodeURIComponent(name)}/activate`),
  update: (name: string, data: Record<string, unknown>) =>
    api.put(`/projects/${encodeURIComponent(name)}`, data),
  delete: (name: string) => api.delete(`/projects/${encodeURIComponent(name)}`),
  active: () => api.get('/projects/active'),
  discover: () => api.post('/projects/discover'),
}

// ── Config ───────────────────────────────────────────────────────────────────
export const configApi = {
  listLLM: () => api.get('/config/llm'),
  saveLLM: (data: Record<string, unknown>) => api.post('/config/llm', data),
  deleteLLM: (name: string) => api.delete(`/config/llm/${encodeURIComponent(name)}`),
  listEmbedding: () => api.get('/config/embedding'),
  saveEmbedding: (data: Record<string, unknown>) => api.post('/config/embedding', data),
  deleteEmbedding: (name: string) =>
    api.delete(`/config/embedding/${encodeURIComponent(name)}`),
  testLLM: () => `/config/llm/test`,
  testEmbedding: () => `/config/embedding/test`,
  getProxy: () => api.get('/config/proxy'),
  saveProxy: (data: { proxy_url: string; proxy_port: string; enabled: boolean }) =>
    api.put('/config/proxy', data),
  getUserProfile: () => api.get('/config/user_profile'),
  saveUserProfile: (profile: string, enabled = true) => api.put('/config/user_profile', { profile, enabled }),
  extractPreferences: (text: string, llm_config_name: string) =>
    api.post('/config/user_profile/extract', { text, llm_config_name }),
  appendProfile: (preferences: string) =>
    api.post('/config/user_profile/append', { preferences }),
}

// ── Presets ──────────────────────────────────────────────────────────────────
export const presetsApi = {
  list: () => api.get('/presets'),
  activate: (name: string) => api.post(`/presets/${encodeURIComponent(name)}/activate`),
  save: (name: string, description = '') => api.post('/presets', { name, description }),
  delete: (name: string) => api.delete(`/presets/${encodeURIComponent(name)}`),
  getPrompts: () => api.get('/presets/prompts'),
  updatePrompt: (key: string, content: string) =>
    api.put(`/presets/prompts/${encodeURIComponent(key)}`, { content }),
  resetPrompt: (key: string) =>
    api.post(`/presets/prompts/${encodeURIComponent(key)}/reset`),
}

// ── Generate (SSE) ────────────────────────────────────────────────────────────

export interface SSEHandle {
  abort: () => void
}

/**
 * 创建一个 EventSource 连接到 SSE 端点（POST via fetch）。
 * 同步返回 SSEHandle，可通过 abort() 取消操作。
 */
export function postSSE(
  url: string,
  body: Record<string, unknown>,
  onProgress: (msg: string, value?: number, content?: string) => void,
  onResult: (content: string) => void,
  onError: (msg: string) => void,
  onDone: () => void,
): SSEHandle {
  const controller = new AbortController()
  let operationId = ''

  const handle: SSEHandle = {
    abort: () => {
      // 通知后端取消
      if (operationId) {
        fetch('/api/generate/cancel', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ operation_id: operationId }),
        }).catch(() => {})
      }
      controller.abort()
    },
  }

  // 异步处理 SSE 流（fire-and-forget）
  ;(async () => {
    try {
      const res = await fetch(`/api${url}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: controller.signal,
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        onError(err.detail ?? res.statusText)
        onDone()
        return
      }

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      const parse = (raw: string) => {
        const lines = raw.split('\n')
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const json = line.slice(6).trim()
          if (!json) continue
          try {
            const event = JSON.parse(json)
            if (event.type === 'started') operationId = event.operation_id ?? ''
            else if (event.type === 'progress') onProgress(event.message ?? '', event.value, event.content)
            else if (event.type === 'result') onResult(event.content ?? '')
            else if (event.type === 'error') onError(event.message ?? '未知错误')
            else if (event.type === 'done') onDone()
          } catch {
            // ignore malformed event
          }
        }
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        buffer = parts.pop() ?? ''
        for (const part of parts) parse(part + '\n\n')
      }
      if (buffer) parse(buffer)
    } catch (e: unknown) {
      // AbortError is normal when user cancels
      if (e instanceof DOMException && e.name === 'AbortError') {
        onDone()
      } else {
        onError((e as Error).message ?? '请求失败')
        onDone()
      }
    }
  })()

  return handle
}

export const generateApi = {
  architecture: (body: Record<string, unknown>) => `/generate/architecture`,
  blueprint: (body: Record<string, unknown>) => `/generate/blueprint`,
  chapter: (body: Record<string, unknown>) => `/generate/chapter`,
  finalize: (body: Record<string, unknown>) => `/generate/finalize`,
  expand: (body: Record<string, unknown>) => `/generate/expand`,
  status: (filepath: string) => api.get(`/generate/status`, { params: { filepath } }),
  chapters: (filepath: string) => api.get(`/generate/chapters`, { params: { filepath } }),
  getChapter: (num: number, filepath: string) =>
    api.get(`/generate/chapter/${num}`, { params: { filepath } }),
  saveChapter: (num: number, content: string, filepath: string) =>
    api.put(`/generate/chapter/${num}`, { content }, { params: { filepath } }),
  saveArchitecture: (content: string, filepath: string) =>
    api.put(`/generate/architecture`, { content, filepath }),
  saveComponent: (component: string, content: string, filepath: string) =>
    api.put(`/generate/architecture/component/${component}`, { content, filepath }),
  saveBlueprint: (content: string, filepath: string) =>
    api.put(`/generate/blueprint`, { content, filepath }),
  saveCharacterDynamics: (content: string, filepath: string) =>
    api.put(`/generate/character_dynamics`, { content, filepath }),
  exportNovel: (filepath: string) =>
    api.get(`/generate/export`, { params: { filepath }, responseType: 'blob' }),
  partialSteps: (filepath: string) =>
    api.get(`/generate/architecture/partial`, { params: { filepath } }),
  assembleArch: (body: Record<string, unknown>) =>
    api.post(`/generate/architecture/assemble`, body),
  continueArch: (body: Record<string, unknown>) => `/generate/architecture/continue`,
  contStepSeed: () => `/generate/architecture/continue/step/seed`,
  contStepWorld: () => `/generate/architecture/continue/step/world`,
  continueStepCharacters: () => `/generate/architecture/continue/step/characters`,
  continueStepArcs: () => `/generate/architecture/continue/step/arcs`,
  continueStepCharState: () => `/generate/architecture/continue/step/char_state`,
  assembleContinuation: (body: Record<string, unknown>) =>
    api.post(`/generate/architecture/continue/assemble`, body),
  compressContext: (body: { llm_config_name: string; filepath: string; include_world_building?: boolean }) =>
    api.post(`/generate/compress-context`, body, { timeout: 600000 }),
  humanize: () => `/generate/humanize`,
  batchHumanize: () => `/generate/humanize/batch`,
  reviseStep: () => `/generate/architecture/step/revise`,
  detailedOutline: () => `/generate/detailed_outline`,
  getDetailedOutline: (filepath: string) =>
    api.get(`/generate/detailed_outline`, { params: { filepath } }),
  saveDetailedOutline: (content: string, filepath: string) =>
    api.put(`/generate/detailed_outline`, { content, filepath }),
  stepCoreSeed: () => `/generate/architecture/step/core_seed`,
  stepCharacters: () => `/generate/architecture/step/characters`,
  stepWorld: () => `/generate/architecture/step/world`,
  stepPlot: () => `/generate/architecture/step/plot`,
}

// ── XP Presets ───────────────────────────────────────────────────────────────
export const xpPresetsApi = {
  list: () => api.get('/xp-presets'),
  create: (name: string, content: string) => api.post('/xp-presets', { name, content }),
  update: (name: string, data: { name?: string; content?: string }) =>
    api.put(`/xp-presets/${encodeURIComponent(name)}`, data),
  delete: (name: string) => api.delete(`/xp-presets/${encodeURIComponent(name)}`),
}

// ── Styles ───────────────────────────────────────────────────────────────────
export const stylesApi = {
  list: () => api.get('/styles'),
  get: (name: string) => api.get(`/styles/${encodeURIComponent(name)}`),
  save: (name: string, data: Record<string, unknown>) =>
    api.put(`/styles/${encodeURIComponent(name)}`, data),
  delete: (name: string) => api.delete(`/styles/${encodeURIComponent(name)}`),
  rollbackCalibration: (name: string) =>
    api.post(`/styles/${encodeURIComponent(name)}/rollback-calibration`),
  analyzeUrl: () => `/styles/analyze`,
  analyzeDNAUrl: () => `/styles/analyze-dna`,
  mergeUrl: () => `/styles/merge`,
  calibrateUrl: () => `/styles/calibrate`,
  calibrateNarrativeUrl: () => `/styles/calibrate-narrative`,
  importAuthorRef: (name: string, formData: FormData) =>
    api.post(`/styles/${encodeURIComponent(name)}/author-reference/import`, formData, {
      headers: { 'Content-Type': undefined },
    }),
  clearAuthorRef: (name: string) =>
    api.delete(`/styles/${encodeURIComponent(name)}/author-reference`),
  authorRefStatus: (name: string) =>
    api.get(`/styles/${encodeURIComponent(name)}/author-reference/status`),
}

// ── Knowledge ─────────────────────────────────────────────────────────────────
export const knowledgeApi = {
  import: (formData: FormData) =>
    api.post('/knowledge/import', formData, {
      headers: { 'Content-Type': undefined },
    }),
  clear: (filepath: string) =>
    api.delete('/knowledge', { params: { filepath } }),
}

// ── Files ────────────────────────────────────────────────────────────────────
export const filesApi = {
  list: (filepath: string) => api.get('/files', { params: { filepath } }),
  content: (filepath: string, path: string) =>
    api.get('/files/content', { params: { filepath, path } }),
}

// ── Logs ─────────────────────────────────────────────────────────────────────
export const logsApi = {
  get: (tail = 200) => api.get('/logs', { params: { tail } }),
  clear: () => api.delete('/logs'),
  getPrompts: (tail = 50, search = '') =>
    api.get('/logs/prompts', { params: { tail, search } }),
  clearPrompts: () => api.delete('/logs/prompts'),
}

// ── Consistency ───────────────────────────────────────────────────────────────
export const consistencyApi = {
  checkUrl: () => `/consistency/check`,
}

// ── Brainstorm ───────────────────────────────────────────────────────────────
export const brainstormApi = {
  chatUrl: () => `/brainstorm/chat`,
}
