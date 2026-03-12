<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { logsApi } from '@/api/client'
import axios from 'axios'

// ── 标签页 ────────────────────────────────────────────────────────────────────
type Tab = 'logs' | 'prompts'
const activeTab = ref<Tab>('logs')

// ── 运行日志 ──────────────────────────────────────────────────────────────────
const logContent = ref('')
const logTailLines = ref(200)
const logLoading = ref(false)

async function loadLogs() {
  logLoading.value = true
  try {
    const res = await logsApi.get(logTailLines.value)
    logContent.value = res.data.content
  } catch (e: unknown) {
    logContent.value = `❌ ${(e as Error).message}`
  } finally {
    logLoading.value = false
  }
}

async function clearLogs() {
  if (!confirm('确认清空运行日志？')) return
  try {
    await logsApi.clear()
    logContent.value = ''
  } catch (e: unknown) {
    logContent.value = `❌ ${(e as Error).message}`
  }
}

// ── Prompt 历史 ───────────────────────────────────────────────────────────────
interface PromptRecord {
  timestamp: string
  model: string
  prompt: string
  response: string
  prompt_len: number
  response_len: number
  reasoning?: string
  reasoning_len?: number
  status?: string   // "pending" | "done" | "error"
  elapsed?: number  // 耗时(秒)
}

const promptRecords = ref<PromptRecord[]>([])
const promptTotal = ref(0)
const promptTail = ref(50)
const promptSearch = ref('')
const promptLoading = ref(false)
const expandedIndex = ref<Set<number>>(new Set())
const expandedReasoning = ref<Set<number>>(new Set())
const expandedResponse = ref<Set<number>>(new Set())

async function loadPrompts() {
  promptLoading.value = true
  try {
    const res = await axios.get('/api/logs/prompts', {
      params: { tail: promptTail.value, search: promptSearch.value },
    })
    promptRecords.value = res.data.records
    promptTotal.value = res.data.total
    expandedIndex.value = new Set()
    expandedReasoning.value = new Set()
    expandedResponse.value = new Set()
  } catch (e: unknown) {
    promptRecords.value = []
  } finally {
    promptLoading.value = false
  }
}

async function clearPrompts() {
  if (!confirm('确认清空所有 Prompt 历史？')) return
  try {
    await axios.delete('/api/logs/prompts')
    promptRecords.value = []
    promptTotal.value = 0
  } catch { /* ignore */ }
}

function togglePrompt(i: number) {
  if (expandedIndex.value.has(i)) expandedIndex.value.delete(i)
  else expandedIndex.value.add(i)
}
function toggleReasoning(i: number) {
  if (expandedReasoning.value.has(i)) expandedReasoning.value.delete(i)
  else expandedReasoning.value.add(i)
}
function toggleResponse(i: number) {
  if (expandedResponse.value.has(i)) expandedResponse.value.delete(i)
  else expandedResponse.value.add(i)
}
function isPromptExpanded(i: number) { return expandedIndex.value.has(i) }
function isReasoningExpanded(i: number) { return expandedReasoning.value.has(i) }
function isResponseExpanded(i: number) { return expandedResponse.value.has(i) }

// ── 复制到剪贴板 ──────────────────────────────────────────────────────────────
const copiedIndex = ref<number | null>(null)
async function copyText(text: string, i: number) {
  try {
    await navigator.clipboard.writeText(text)
    copiedIndex.value = i
    setTimeout(() => { copiedIndex.value = null }, 1500)
  } catch { /* ignore */ }
}

// 截取预览（前200字）
function preview(text: string, len = 200) {
  return text.length > len ? text.slice(0, len) + '…' : text
}

// 格式化字数
function fmtLen(n: number) {
  return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : `${n}`
}

onMounted(() => {
  loadLogs()
  loadPrompts()
})
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 py-6 space-y-4">
    <h2 class="text-2xl font-bold" style="color: var(--color-ink)">📜 日志</h2>

    <!-- 标签页切换 -->
    <div class="flex gap-1 border-b border-[var(--color-parchment-darker)]">
      <button
        v-for="tab in [{ key: 'logs', label: '运行日志' }, { key: 'prompts', label: 'Prompt 历史' }]"
        :key="tab.key"
        @click="activeTab = tab.key as Tab"
        class="px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px"
        :class="activeTab === tab.key
          ? 'border-[var(--color-leather)] text-[var(--color-leather)]'
          : 'border-transparent text-[var(--color-ink-light)] hover:text-[var(--color-ink)]'"
        type="button"
      >
        {{ tab.label }}
        <span
          v-if="tab.key === 'prompts' && promptTotal > 0"
          class="ml-1 px-1.5 py-0.5 rounded-full text-xs font-normal"
          style="background-color: var(--color-parchment-dark); color: var(--color-ink-light)"
        >{{ promptTotal }}</span>
      </button>
    </div>

    <!-- ── 运行日志 ──────────────────────────────────────────────────────────── -->
    <div v-if="activeTab === 'logs'" class="space-y-3">
      <div class="flex items-center gap-2 flex-wrap">
        <label class="text-sm text-[var(--color-ink-light)]">显示最后</label>
        <input
          v-model.number="logTailLines" type="number" min="10" max="5000"
          class="w-20 border border-[var(--color-parchment-darker)] rounded-md px-2 py-1 text-sm"
        />
        <label class="text-sm text-[var(--color-ink-light)]">行</label>
        <button @click="loadLogs" :disabled="logLoading"
          class="border border-[var(--color-parchment-darker)] rounded-md px-3 py-1.5 text-sm hover:bg-[var(--color-parchment)] disabled:opacity-50 transition-colors" type="button">
          🔄 刷新
        </button>
        <button @click="clearLogs"
          class="border border-red-200 text-red-600 rounded-md px-3 py-1.5 text-sm hover:bg-red-50 transition-colors" type="button">
          清空
        </button>
      </div>

      <div
        class="rounded-xl border border-[var(--color-parchment-darker)] overflow-auto font-mono text-xs leading-relaxed"
        style="background-color: var(--color-spine); color: var(--color-parchment-dark); max-height: calc(100vh - 220px); min-height: 400px;"
      >
        <div v-if="logLoading" class="p-4 italic opacity-50">加载中…</div>
        <pre v-else-if="logContent" class="p-4 whitespace-pre-wrap">{{ logContent }}</pre>
        <div v-else class="p-4 italic opacity-50">日志为空</div>
      </div>
    </div>

    <!-- ── Prompt 历史 ───────────────────────────────────────────────────────── -->
    <div v-if="activeTab === 'prompts'" class="space-y-3">
      <!-- 工具栏 -->
      <div class="flex items-center gap-2 flex-wrap">
        <input
          v-model="promptSearch"
          @keyup.enter="loadPrompts"
          placeholder="搜索 prompt/response 关键词…"
          class="flex-1 min-w-48 border border-[var(--color-parchment-darker)] rounded-md px-3 py-1.5 text-sm"
        />
        <label class="text-sm text-[var(--color-ink-light)]">显示最新</label>
        <input
          v-model.number="promptTail" type="number" min="5" max="500"
          class="w-16 border border-[var(--color-parchment-darker)] rounded-md px-2 py-1 text-sm"
        />
        <label class="text-sm text-[var(--color-ink-light)]">条</label>
        <button @click="loadPrompts" :disabled="promptLoading"
          class="border border-[var(--color-parchment-darker)] rounded-md px-3 py-1.5 text-sm hover:bg-[var(--color-parchment)] disabled:opacity-50 transition-colors" type="button">
          🔄 刷新
        </button>
        <button @click="clearPrompts"
          class="border border-red-200 text-red-600 rounded-md px-3 py-1.5 text-sm hover:bg-red-50 transition-colors" type="button">
          清空历史
        </button>
      </div>

      <!-- 统计 -->
      <p v-if="!promptLoading" class="text-xs text-[var(--color-ink-light)]">
        共 {{ promptTotal }} 条记录，当前显示 {{ promptRecords.length }} 条
        <span v-if="promptSearch">（已过滤）</span>
      </p>

      <!-- 加载中 -->
      <div v-if="promptLoading" class="text-sm text-[var(--color-ink-light)] italic py-8 text-center">
        加载中…
      </div>

      <!-- 空状态 -->
      <div
        v-else-if="promptRecords.length === 0"
        class="rounded-xl border border-[var(--color-parchment-darker)] bg-white p-12 text-center"
      >
        <p class="text-[var(--color-ink-light)] text-sm">
          {{ promptSearch ? '未找到匹配记录' : '暂无 Prompt 历史。生成内容后，记录将在此显示。' }}
        </p>
      </div>

      <!-- 记录列表 -->
      <div v-else class="space-y-3">
        <div
          v-for="(record, i) in promptRecords"
          :key="i"
          class="rounded-xl border border-[var(--color-parchment-darker)] bg-white overflow-hidden"
        >
          <!-- 记录头部 -->
          <div
            class="flex items-center gap-3 px-4 py-3 cursor-pointer select-none hover:bg-[var(--color-parchment)] transition-colors"
            style="background-color: var(--color-parchment)"
            @click="togglePrompt(i)"
          >
            <!-- 序号 -->
            <span
              class="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold"
              style="background-color: var(--color-gold-dark); color: var(--color-parchment)"
            >
              {{ promptRecords.length - i }}
            </span>

            <!-- 元信息 -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-xs font-medium" style="color: var(--color-leather)">
                  {{ record.timestamp }}
                </span>
                <span
                  v-if="record.model"
                  class="px-2 py-0.5 rounded text-xs"
                  style="background-color: var(--color-parchment-dark); color: var(--color-ink-light)"
                >
                  {{ record.model }}
                </span>
                <span v-if="record.status === 'pending'" class="px-1.5 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-700 animate-pulse">
                  等待返回…
                </span>
                <span v-else-if="record.status === 'error'" class="px-1.5 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700">
                  失败
                </span>
                <span class="text-xs" style="color: var(--color-ink-light)">
                  Prompt {{ fmtLen(record.prompt_len) }}字
                  <template v-if="record.status !== 'pending'">
                    <template v-if="record.reasoning_len"> · 思考 {{ fmtLen(record.reasoning_len) }}字</template>
                    · 回复 {{ fmtLen(record.response_len) }}字
                  </template>
                  <template v-if="record.elapsed"> · {{ record.elapsed }}s</template>
                </span>
              </div>
              <!-- Prompt 预览 -->
              <p class="text-xs mt-0.5 truncate" style="color: var(--color-ink-light)">
                {{ preview(record.prompt, 120) }}
              </p>
            </div>

            <!-- 展开箭头 -->
            <svg
              class="flex-shrink-0 w-4 h-4 transition-transform"
              :class="isPromptExpanded(i) ? 'rotate-180' : ''"
              style="color: var(--color-leather)"
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </div>

          <!-- 展开内容 -->
          <Transition name="slide">
            <div v-if="isPromptExpanded(i)" class="border-t border-[var(--color-parchment-darker)]">

              <!-- Prompt 区 -->
              <div class="px-4 pt-3 pb-2">
                <div class="flex items-center justify-between mb-1.5">
                  <span class="text-xs font-semibold uppercase tracking-wide" style="color: var(--color-leather)">
                    Prompt
                  </span>
                  <button
                    @click="copyText(record.prompt, i * 3 + 1)"
                    class="text-xs px-2 py-0.5 rounded border transition-colors"
                    style="border-color: var(--color-parchment-darker); color: var(--color-ink-light)"
                    type="button"
                  >
                    {{ copiedIndex === i * 3 + 1 ? '✓ 已复制' : '复制' }}
                  </button>
                </div>
                <pre
                  class="text-xs font-mono whitespace-pre-wrap leading-relaxed rounded-lg p-3 overflow-auto"
                  style="background-color: var(--color-spine); color: var(--color-parchment-dark); max-height: 400px"
                >{{ record.prompt }}</pre>
              </div>

              <!-- 思考过程（仅思考模型显示） -->
              <template v-if="record.reasoning">
                <div class="flex items-center gap-2 px-4 py-2 border-t border-[var(--color-parchment-darker)]">
                  <span class="text-xs font-semibold uppercase tracking-wide" style="color: #b8860b">
                    Reasoning
                  </span>
                  <span class="text-xs" style="color: var(--color-ink-light)">
                    {{ fmtLen(record.reasoning_len || 0) }} 字
                  </span>
                  <button
                    @click="toggleReasoning(i)"
                    class="ml-auto text-xs px-2 py-0.5 rounded border transition-colors"
                    style="border-color: var(--color-parchment-darker); color: var(--color-ink-light)"
                    type="button"
                  >
                    {{ isReasoningExpanded(i) ? '收起思考' : '展开思考' }}
                  </button>
                  <button
                    @click="copyText(record.reasoning!, i * 3)"
                    class="text-xs px-2 py-0.5 rounded border transition-colors"
                    style="border-color: var(--color-parchment-darker); color: var(--color-ink-light)"
                    type="button"
                  >
                    {{ copiedIndex === i * 3 ? '✓ 已复制' : '复制' }}
                  </button>
                </div>
                <div class="px-4 pb-3">
                  <Transition name="slide">
                    <pre
                      v-if="isReasoningExpanded(i)"
                      class="text-xs font-mono whitespace-pre-wrap leading-relaxed rounded-lg p-3 overflow-auto"
                      style="background-color: #2a2a1a; color: #d4c87a; max-height: 520px"
                    >{{ record.reasoning }}</pre>
                    <p
                      v-else
                      class="text-xs italic rounded-lg p-3"
                      style="background-color: var(--color-parchment); color: var(--color-ink-light)"
                    >
                      {{ preview(record.reasoning!, 300) }}
                    </p>
                  </Transition>
                </div>
              </template>

              <!-- 分隔线 + 展开回复按钮 -->
              <div class="flex items-center gap-2 px-4 py-2 border-t border-[var(--color-parchment-darker)]">
                <span class="text-xs font-semibold uppercase tracking-wide" style="color: var(--color-success)">
                  Response
                </span>
                <span class="text-xs" style="color: var(--color-ink-light)">
                  {{ fmtLen(record.response_len) }} 字
                </span>
                <button
                  @click="toggleResponse(i)"
                  class="ml-auto text-xs px-2 py-0.5 rounded border transition-colors"
                  style="border-color: var(--color-parchment-darker); color: var(--color-ink-light)"
                  type="button"
                >
                  {{ isResponseExpanded(i) ? '收起回复' : '展开回复' }}
                </button>
                <button
                  @click="copyText(record.response, i * 3 + 2)"
                  class="text-xs px-2 py-0.5 rounded border transition-colors"
                  style="border-color: var(--color-parchment-darker); color: var(--color-ink-light)"
                  type="button"
                >
                  {{ copiedIndex === i * 3 + 2 ? '✓ 已复制' : '复制' }}
                </button>
              </div>

              <!-- 回复内容（默认折叠，仅显示预览） -->
              <div class="px-4 pb-3">
                <Transition name="slide">
                  <pre
                    v-if="isResponseExpanded(i)"
                    class="text-xs font-mono whitespace-pre-wrap leading-relaxed rounded-lg p-3 overflow-auto"
                    style="background-color: #1a2e1a; color: #a8d5a2; max-height: 520px"
                  >{{ record.response }}</pre>
                  <p
                    v-else
                    class="text-xs italic rounded-lg p-3"
                    style="background-color: var(--color-parchment); color: var(--color-ink-light)"
                  >
                    {{ preview(record.response, 300) }}
                  </p>
                </Transition>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </div>
  </div>
</template>
