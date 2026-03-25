<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { configApi, postSSE } from '@/api/client'
import { useConfigStore } from '@/stores/config'

const configStore = useConfigStore()
const statusMsg = ref('')

// ── 连通性测试 ──────────────────────────────────────────────────────────────
const llmTestRunning = ref(false)
const llmTestResult = ref('')
const embTestRunning = ref(false)
const embTestResult = ref('')

function testLLM() {
  llmTestRunning.value = true
  llmTestResult.value = ''
  postSSE(
    configApi.testLLM(),
    {
      interface_format: llmForm.value.interface_format,
      api_key: llmForm.value.api_key,
      base_url: llmForm.value.base_url,
      model_name: llmForm.value.model_name,
      temperature: llmForm.value.temperature,
      max_tokens: llmForm.value.max_tokens,
      timeout: llmForm.value.timeout,
    },
    (msg) => { llmTestResult.value = msg },
    (content) => { llmTestResult.value = content },
    (err) => { llmTestResult.value = `❌ ${err}`; llmTestRunning.value = false },
    () => { llmTestRunning.value = false },
  )
}

function testEmb() {
  embTestRunning.value = true
  embTestResult.value = ''
  postSSE(
    configApi.testEmbedding(),
    {
      interface_format: embForm.value.interface_format,
      api_key: embForm.value.api_key,
      base_url: embForm.value.base_url,
      model_name: embForm.value.model_name,
    },
    (msg) => { embTestResult.value = msg },
    (content) => { embTestResult.value = content },
    (err) => { embTestResult.value = `❌ ${err}`; embTestRunning.value = false },
    () => { embTestRunning.value = false },
  )
}

// ── LLM ──────────────────────────────────────────────────────────────────────
const selectedLLM = ref('')
const llmForm = ref({
  config_name: '',
  api_key: '',
  base_url: '',
  interface_format: 'OpenAI',
  model_name: '',
  temperature: 0.7,
  max_tokens: 4096,
  timeout: 600,
  enable_thinking: false,
  thinking_budget: 0,
  enable_streaming: true,
})

const interfaceFormats = ['OpenAI', 'Claude', 'Gemini', 'Ollama', 'Azure']

function loadLLMConfig(name: string) {
  if (!name) return
  const c = configStore.llmConfigs[name]
  if (!c) return
  llmForm.value = {
    config_name: name,
    api_key: (c.api_key as string) ?? '',
    base_url: (c.base_url as string) ?? '',
    interface_format: (c.interface_format as string) ?? 'OpenAI',
    model_name: (c.model_name as string) ?? '',
    temperature: (c.temperature as number) ?? 0.7,
    max_tokens: (c.max_tokens as number) ?? 4096,
    timeout: (c.timeout as number) ?? 600,
    enable_thinking: (c.enable_thinking as boolean) ?? false,
    thinking_budget: (c.thinking_budget as number) ?? 0,
    enable_streaming: (c.enable_streaming as boolean) ?? true,
  }
}

async function saveLLM() {
  try {
    await configApi.saveLLM(llmForm.value as Record<string, unknown>)
    await configStore.loadAll()
    statusMsg.value = `✅ LLM 配置「${llmForm.value.config_name}」已保存`
  } catch (e: unknown) {
    statusMsg.value = `❌ ${(e as Error).message}`
  }
}

async function deleteLLM() {
  if (!selectedLLM.value) return
  if (!confirm(`确认删除配置「${selectedLLM.value}」？`)) return
  try {
    await configApi.deleteLLM(selectedLLM.value)
    await configStore.loadAll()
    selectedLLM.value = ''
    statusMsg.value = `✅ 已删除`
  } catch (e: unknown) {
    statusMsg.value = `❌ ${(e as Error).message}`
  }
}

// ── Embedding ─────────────────────────────────────────────────────────────────
const selectedEmb = ref('')
const embForm = ref({
  config_name: '',
  interface_format: 'OpenAI',
  api_key: '',
  base_url: '',
  model_name: '',
  retrieval_k: 4,
})

function loadEmbConfig(name: string) {
  if (!name) return
  const c = configStore.embeddingConfigs[name]
  if (!c) return
  embForm.value = {
    config_name: name,
    interface_format: (c.interface_format as string) ?? 'OpenAI',
    api_key: (c.api_key as string) ?? '',
    base_url: (c.base_url as string) ?? '',
    model_name: (c.model_name as string) ?? '',
    retrieval_k: (c.retrieval_k as number) ?? 4,
  }
}

async function saveEmb() {
  try {
    await configApi.saveEmbedding(embForm.value as Record<string, unknown>)
    await configStore.loadAll()
    statusMsg.value = `✅ Embedding 配置「${embForm.value.config_name}」已保存`
  } catch (e: unknown) {
    statusMsg.value = `❌ ${(e as Error).message}`
  }
}

async function deleteEmb() {
  if (!selectedEmb.value) return
  if (!confirm(`确认删除配置「${selectedEmb.value}」？`)) return
  try {
    await configApi.deleteEmbedding(selectedEmb.value)
    await configStore.loadAll()
    selectedEmb.value = ''
    statusMsg.value = `✅ 已删除`
  } catch (e: unknown) {
    statusMsg.value = `❌ ${(e as Error).message}`
  }
}

onMounted(() => configStore.loadAll())
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-6 space-y-6">
    <h2 class="text-2xl font-bold" style="color: var(--color-ink)">⚙️ 模型配置</h2>

    <Transition name="fade">
      <div v-if="statusMsg" class="px-4 py-2 rounded-md text-sm"
        :class="statusMsg.startsWith('✅') ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'">
        {{ statusMsg }}
      </div>
    </Transition>

    <!-- LLM 配置 -->
    <div class="rounded-xl border border-[var(--color-parchment-darker)] bg-white overflow-hidden">
      <div class="px-5 py-3 bg-[var(--color-parchment)] border-b border-[var(--color-parchment-darker)]">
        <h3 class="font-semibold text-[var(--color-leather)]">LLM 配置</h3>
      </div>
      <div class="p-5 space-y-4">
        <div class="flex gap-2 flex-wrap">
          <select
            v-model="selectedLLM"
            @change="loadLLMConfig(selectedLLM)"
            class="border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm flex-1"
          >
            <option value="">— 选择已有配置 —</option>
            <option v-for="c in configStore.llmChoices" :key="c" :value="c">{{ c }}</option>
          </select>
          <button @click="selectedLLM = ''; llmForm = { config_name: '', api_key: '', base_url: '', interface_format: 'OpenAI', model_name: '', temperature: 0.7, max_tokens: 4096, timeout: 600, enable_thinking: false, thinking_budget: 0, enable_streaming: true }"
            class="border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm hover:bg-[var(--color-parchment)] transition-colors" type="button">
            + 新建
          </button>
          <button @click="deleteLLM" :disabled="!selectedLLM"
            class="border border-red-200 text-red-600 rounded-md px-3 py-2 text-sm hover:bg-red-50 disabled:opacity-40 transition-colors" type="button">
            删除
          </button>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs text-[var(--color-ink-light)] mb-1">配置名称 *</label>
            <input v-model="llmForm.config_name" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
          </div>
          <div>
            <label class="block text-xs text-[var(--color-ink-light)] mb-1">接口格式</label>
            <select v-model="llmForm.interface_format" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm">
              <option v-for="f in interfaceFormats" :key="f" :value="f">{{ f }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs text-[var(--color-ink-light)] mb-1">API Key</label>
            <input v-model="llmForm.api_key" type="password" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
          </div>
          <div>
            <label class="block text-xs text-[var(--color-ink-light)] mb-1">Base URL</label>
            <input v-model="llmForm.base_url" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
          </div>
          <div>
            <label class="block text-xs text-[var(--color-ink-light)] mb-1">模型名称</label>
            <input v-model="llmForm.model_name" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
          </div>
          <div>
            <label class="block text-xs text-[var(--color-ink-light)] mb-1">Temperature ({{ llmForm.temperature }})</label>
            <input v-model.number="llmForm.temperature" type="range" min="0" max="2" step="0.05" class="w-full accent-[var(--color-leather)]" />
          </div>
          <div>
            <label class="block text-xs text-[var(--color-ink-light)] mb-1">Max Tokens</label>
            <input v-model.number="llmForm.max_tokens" type="number" min="256" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
          </div>
          <div>
            <label class="block text-xs text-[var(--color-ink-light)] mb-1">超时 (秒)</label>
            <input v-model.number="llmForm.timeout" type="number" min="10" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
          </div>
          <div class="flex items-center gap-3">
            <label class="flex items-center gap-2 text-sm cursor-pointer select-none">
              <input type="checkbox" v-model="llmForm.enable_thinking" class="accent-[var(--color-leather)]" />
              启用 Thinking 模式
            </label>
          </div>
          <div class="flex items-center gap-3">
            <label class="flex items-center gap-2 text-sm cursor-pointer select-none">
              <input type="checkbox" v-model="llmForm.enable_streaming" class="accent-[var(--color-leather)]" />
              流式输出
            </label>
            <span class="text-xs text-[var(--color-ink-light)]">实时显示生成进度，超时时保留已生成内容</span>
          </div>
          <div v-if="llmForm.enable_thinking">
            <label class="block text-xs text-[var(--color-ink-light)] mb-1">Thinking Budget</label>
            <input v-model.number="llmForm.thinking_budget" type="number" min="0" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
          </div>
        </div>
        <div class="flex justify-end gap-2">
          <button @click="testLLM" :disabled="llmTestRunning || !llmForm.model_name"
            class="px-4 py-2 rounded-md text-sm font-semibold border border-[var(--color-leather)] text-[var(--color-leather)] hover:bg-[var(--color-parchment)] disabled:opacity-40 transition-colors" type="button">
            {{ llmTestRunning ? '测试中...' : '测试连接' }}
          </button>
          <button @click="saveLLM" class="px-5 py-2 rounded-md text-sm font-semibold transition-colors" style="background-color: var(--color-leather); color: var(--color-parchment);" type="button">
            保存 LLM 配置
          </button>
        </div>
        <div v-if="llmTestResult" class="px-4 py-2 rounded-md text-sm"
          :class="llmTestResult.startsWith('✅') ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'">
          {{ llmTestResult }}
        </div>
      </div>
    </div>

    <!-- Embedding 配置 -->
    <div class="rounded-xl border border-[var(--color-parchment-darker)] bg-white overflow-hidden">
      <div class="px-5 py-3 bg-[var(--color-parchment)] border-b border-[var(--color-parchment-darker)]">
        <h3 class="font-semibold text-[var(--color-leather)]">Embedding 配置</h3>
      </div>
      <div class="p-5 space-y-4">
        <div class="flex gap-2 flex-wrap">
          <select
            v-model="selectedEmb"
            @change="loadEmbConfig(selectedEmb)"
            class="border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm flex-1"
          >
            <option value="">— 选择已有配置 —</option>
            <option v-for="c in configStore.embeddingChoices" :key="c" :value="c">{{ c }}</option>
          </select>
          <button @click="selectedEmb = ''; embForm = { config_name: '', interface_format: 'OpenAI', api_key: '', base_url: '', model_name: '', retrieval_k: 4 }"
            class="border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm hover:bg-[var(--color-parchment)] transition-colors" type="button">
            + 新建
          </button>
          <button @click="deleteEmb" :disabled="!selectedEmb"
            class="border border-red-200 text-red-600 rounded-md px-3 py-2 text-sm hover:bg-red-50 disabled:opacity-40 transition-colors" type="button">
            删除
          </button>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs text-[var(--color-ink-light)] mb-1">配置名称 *</label>
            <input v-model="embForm.config_name" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
          </div>
          <div>
            <label class="block text-xs text-[var(--color-ink-light)] mb-1">接口格式</label>
            <select v-model="embForm.interface_format" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm">
              <option v-for="f in interfaceFormats" :key="f" :value="f">{{ f }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs text-[var(--color-ink-light)] mb-1">API Key</label>
            <input v-model="embForm.api_key" type="password" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
          </div>
          <div>
            <label class="block text-xs text-[var(--color-ink-light)] mb-1">Base URL</label>
            <input v-model="embForm.base_url" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
          </div>
          <div>
            <label class="block text-xs text-[var(--color-ink-light)] mb-1">模型名称</label>
            <input v-model="embForm.model_name" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
          </div>
          <div>
            <label class="block text-xs text-[var(--color-ink-light)] mb-1">检索 TopK</label>
            <input v-model.number="embForm.retrieval_k" type="number" min="1" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
          </div>
        </div>
        <div class="flex justify-end gap-2">
          <button @click="testEmb" :disabled="embTestRunning || !embForm.model_name"
            class="px-4 py-2 rounded-md text-sm font-semibold border border-[var(--color-leather)] text-[var(--color-leather)] hover:bg-[var(--color-parchment)] disabled:opacity-40 transition-colors" type="button">
            {{ embTestRunning ? '测试中...' : '测试连接' }}
          </button>
          <button @click="saveEmb" class="px-5 py-2 rounded-md text-sm font-semibold transition-colors" style="background-color: var(--color-leather); color: var(--color-parchment);" type="button">
            保存 Embedding 配置
          </button>
        </div>
        <div v-if="embTestResult" class="px-4 py-2 rounded-md text-sm"
          :class="embTestResult.startsWith('✅') ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'">
          {{ embTestResult }}
        </div>
      </div>
    </div>
  </div>
</template>
