<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { useWorkshopState } from '@/composables/useWorkshopState'
import { xpPresetsApi } from '@/api/client'

const props = defineProps<{ state: ReturnType<typeof useWorkshopState> }>()

// XP 预设相关状态
type XPPreset = { name: string; content: string }
const xpPresets = ref<XPPreset[]>([])
const showXPManager = ref(false)
const editingXP = ref<XPPreset | null>(null)
const newXPName = ref('')
const newXPContent = ref('')
const xpSaving = ref(false)

// 选中列表直接用 state.xpSelectedPresets（持久化到项目数据）
function syncXpTypeFromSelection() {
  const parts: string[] = []
  for (const name of props.state.xpSelectedPresets.value) {
    const preset = xpPresets.value.find(p => p.name === name)
    if (preset) {
      parts.push(`【${preset.name}】\n${preset.content}`)
    }
  }
  props.state.xpType.value = parts.join('\n\n')
}

function toggleXP(name: string) {
  const list = props.state.xpSelectedPresets.value
  const idx = list.indexOf(name)
  if (idx >= 0) {
    list.splice(idx, 1)
  } else {
    list.push(name)
  }
  syncXpTypeFromSelection()
}

async function loadPresets() {
  try {
    const res = await xpPresetsApi.list()
    xpPresets.value = res.data.presets
    // 加载后根据已存储的选中列表重建 xpType
    if (props.state.xpSelectedPresets.value.length) {
      syncXpTypeFromSelection()
    }
  } catch { /* ignore */ }
}

async function saveXP() {
  const name = (editingXP.value ? (newXPName.value || editingXP.value.name) : newXPName.value).trim()
  const content = newXPContent.value.trim()
  if (!name || !content) return
  xpSaving.value = true
  try {
    if (editingXP.value) {
      const oldName = editingXP.value.name
      await xpPresetsApi.update(oldName, { name, content })
      // 如果改了名，同步更新选中列表
      if (oldName !== name) {
        const list = props.state.xpSelectedPresets.value
        const idx = list.indexOf(oldName)
        if (idx >= 0) list[idx] = name
      }
    } else {
      await xpPresetsApi.create(name, content)
    }
    await loadPresets()
    cancelEdit()
    syncXpTypeFromSelection()
  } catch (e: unknown) {
    alert((e as Error).message)
  }
  xpSaving.value = false
}

async function deleteXP(name: string) {
  if (!confirm(`确认删除 XP 预设「${name}」？`)) return
  try {
    await xpPresetsApi.delete(name)
    const list = props.state.xpSelectedPresets.value
    const idx = list.indexOf(name)
    if (idx >= 0) list.splice(idx, 1)
    await loadPresets()
    syncXpTypeFromSelection()
  } catch (e: unknown) {
    alert((e as Error).message)
  }
}

function startEdit(preset: XPPreset) {
  editingXP.value = preset
  newXPName.value = preset.name
  newXPContent.value = preset.content
  showXPManager.value = true
}

function startCreate() {
  editingXP.value = null
  newXPName.value = ''
  newXPContent.value = ''
  showXPManager.value = true
}

function cancelEdit() {
  editingXP.value = null
  newXPName.value = ''
  newXPContent.value = ''
  showXPManager.value = false
}

onMounted(loadPresets)
</script>

<template>
  <div class="rounded-xl border border-[var(--color-parchment-darker)] bg-white p-5 space-y-4">
    <h3 class="font-semibold text-[var(--color-leather)]">基础参数</h3>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div>
        <label class="block text-xs text-[var(--color-ink-light)] mb-1">LLM 配置</label>
        <select v-model="state.llmConfig.value" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm">
          <option v-for="c in state.configStore.llmChoices" :key="c" :value="c">{{ c }}</option>
        </select>
      </div>
      <div>
        <label class="block text-xs text-[var(--color-ink-light)] mb-1">Embedding 配置</label>
        <select v-model="state.embConfig.value" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm">
          <option v-for="c in state.configStore.embeddingChoices" :key="c" :value="c">{{ c }}</option>
        </select>
      </div>
      <div>
        <label class="block text-xs text-[var(--color-ink-light)] mb-1">题材/主题</label>
        <input v-model="state.topic.value" placeholder="请输入小说主题…" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
      </div>
      <div>
        <label class="block text-xs text-[var(--color-ink-light)] mb-1">类型</label>
        <input v-model="state.genre.value" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
      </div>
      <div>
        <label class="block text-xs text-[var(--color-ink-light)] mb-1">章节数</label>
        <input v-model.number="state.numChapters.value" type="number" min="1" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
      </div>
      <div>
        <label class="block text-xs text-[var(--color-ink-light)] mb-1">每章字数</label>
        <input v-model.number="state.wordNumber.value" type="number" min="500" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
      </div>

      <!-- XP 类型/核心玩法 -->
      <div class="sm:col-span-2 space-y-2">
        <div class="flex items-center justify-between">
          <label class="block text-xs text-[var(--color-ink-light)]">XP类型/核心玩法（可多选）</label>
          <button @click="startCreate()" class="text-xs text-blue-600 hover:text-blue-800" type="button">+ 新建预设</button>
        </div>

        <!-- 预设选择区 -->
        <div v-if="xpPresets.length" class="flex flex-wrap gap-2">
          <label
            v-for="preset in xpPresets" :key="preset.name"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm cursor-pointer transition-colors border"
            :class="state.xpSelectedPresets.value.includes(preset.name)
              ? 'bg-blue-50 border-blue-300 text-blue-700'
              : 'bg-white border-[var(--color-parchment-darker)] text-[var(--color-ink-light)] hover:border-blue-200'"
          >
            <input
              type="checkbox"
              :checked="state.xpSelectedPresets.value.includes(preset.name)"
              @change="toggleXP(preset.name)"
              class="sr-only"
            />
            <span>{{ preset.name }}</span>
            <button
              @click.prevent.stop="startEdit(preset)"
              class="text-gray-400 hover:text-blue-500 ml-0.5"
              type="button" title="编辑"
            >&#9998;</button>
            <button
              @click.prevent.stop="deleteXP(preset.name)"
              class="text-gray-400 hover:text-red-500"
              type="button" title="删除"
            >&times;</button>
          </label>
        </div>
        <p v-else class="text-xs text-[var(--color-ink-light)]">暂无 XP 预设，点击「新建预设」创建。也可在下方直接输入。</p>

        <!-- 新建/编辑面板 -->
        <div v-if="showXPManager" class="border border-blue-200 rounded-lg p-3 bg-blue-50/30 space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium">{{ editingXP ? '编辑预设' : '新建 XP 预设' }}</span>
            <button @click="cancelEdit()" class="text-xs text-gray-500 hover:text-gray-700" type="button">取消</button>
          </div>
          <input
            v-model="newXPName"
            placeholder="预设名称，如：催眠、NTR、时间停止…"
            class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-1.5 text-sm"
          />
          <textarea
            v-model="newXPContent"
            rows="4"
            placeholder="详细描述该 XP 类型的定义、卖点、关键元素…"
            class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm resize-y"
          />
          <div class="flex justify-end">
            <button
              @click="saveXP()"
              :disabled="xpSaving || !newXPName.trim() || !newXPContent.trim()"
              class="btn-primary text-sm"
              type="button"
            >
              {{ xpSaving ? '保存中…' : (editingXP ? '更新预设' : '保存预设') }}
            </button>
          </div>
        </div>

        <!-- 合并结果预览/手动编辑 -->
        <details class="text-sm">
          <summary class="text-xs text-[var(--color-ink-light)] cursor-pointer select-none">
            展开查看/手动编辑 XP 合并文本
          </summary>
          <textarea
            v-model="state.xpType.value"
            rows="3"
            placeholder="可留空，或选择上方预设自动填充"
            class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm resize-y mt-1"
          />
        </details>
      </div>

      <div class="sm:col-span-2">
        <label class="block text-xs text-[var(--color-ink-light)] mb-1">全局创作指导</label>
        <textarea v-model="state.userGuidance.value" rows="3" placeholder="整体写作风格、重点注意事项…" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm resize-y" />
      </div>
    </div>
  </div>
</template>
