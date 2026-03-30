<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { diffLines } from 'diff'
import type { useWorkshopState } from '@/composables/useWorkshopState'
import StepCard from '@/components/StepCard.vue'

const props = defineProps<{ state: ReturnType<typeof useWorkshopState> }>()

// ── paragraph-aligned diff ──

/** Split text into paragraphs (by blank lines) preserving trailing newlines */
function splitParas(text: string): string[] {
  if (!text) return []
  // Split on one or more blank lines, keep each paragraph as a unit
  return text.split(/\n{2,}/).map(p => p.trim()).filter(Boolean)
}

interface AlignedRow {
  oldPara: string   // original paragraph (empty if added)
  newPara: string   // new paragraph (empty if removed)
  type: 'equal' | 'modified' | 'added' | 'removed'
}

const alignedRows = computed<AlignedRow[]>(() => {
  const oldText = props.state.expandOriginal.value || ''
  const newText = props.state.expandNew.value || ''
  if (!oldText && !newText) return []

  // Use diffLines to get paragraph-level changes
  const diffs = diffLines(oldText, newText)
  const rows: AlignedRow[] = []
  let i = 0
  while (i < diffs.length) {
    const d = diffs[i]
    if (!d.added && !d.removed) {
      // Unchanged block - split into paragraphs
      for (const p of splitParas(d.value)) {
        rows.push({ oldPara: p, newPara: p, type: 'equal' })
      }
      i++
    } else if (d.removed && i + 1 < diffs.length && diffs[i + 1].added) {
      // Removed + Added pair = modification
      const oldParas = splitParas(d.value)
      const newParas = splitParas(diffs[i + 1].value)
      const maxLen = Math.max(oldParas.length, newParas.length)
      for (let j = 0; j < maxLen; j++) {
        rows.push({
          oldPara: oldParas[j] || '',
          newPara: newParas[j] || '',
          type: 'modified',
        })
      }
      i += 2
    } else if (d.removed) {
      for (const p of splitParas(d.value)) {
        rows.push({ oldPara: p, newPara: '', type: 'removed' })
      }
      i++
    } else if (d.added) {
      for (const p of splitParas(d.value)) {
        rows.push({ oldPara: '', newPara: p, type: 'added' })
      }
      i++
    } else {
      i++
    }
  }
  return rows
})

function escapeHtml(s: string) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br/>')
}

/** For modified rows, produce character-level diff HTML */
import { diffChars } from 'diff'

function charDiffHtml(oldStr: string, newStr: string, side: 'new' | 'old'): string {
  if (!oldStr && !newStr) return ''
  if (!oldStr) return `<span class="diff-add">${escapeHtml(newStr)}</span>`
  if (!newStr) return `<span class="diff-del">${escapeHtml(oldStr)}</span>`
  const parts = diffChars(oldStr, newStr)
  if (side === 'new') {
    return parts.filter(p => !p.removed).map(p => {
      const e = escapeHtml(p.value)
      return p.added ? `<span class="diff-add">${e}</span>` : e
    }).join('')
  } else {
    return parts.filter(p => !p.added).map(p => {
      const e = escapeHtml(p.value)
      return p.removed ? `<span class="diff-del">${e}</span>` : e
    }).join('')
  }
}

// ── scroll sync (simple scrollTop sync for aligned rows) ──
const leftPanel = ref<HTMLElement | null>(null)
const rightPanel = ref<HTMLElement | null>(null)
let syncing = false

function syncScroll(source: HTMLElement, target: HTMLElement) {
  if (syncing) return
  syncing = true
  target.scrollTop = source.scrollTop
  requestAnimationFrame(() => { syncing = false })
}

function onLeftScroll() {
  if (leftPanel.value && rightPanel.value) syncScroll(leftPanel.value, rightPanel.value)
}
function onRightScroll() {
  if (rightPanel.value && leftPanel.value) syncScroll(rightPanel.value, leftPanel.value)
}

// ── editor panel ──
const editTarget = ref<'new' | 'old'>('old')
const editText = ref('')
const editDirty = ref(false)

// Load text into editor when target changes or when results arrive
function loadEditText() {
  editText.value = editTarget.value === 'new'
    ? (props.state.expandNew.value || '')
    : (props.state.expandOriginal.value || '')
  editDirty.value = false
}

watch(editTarget, loadEditText)
watch(() => [props.state.expandNew.value, props.state.expandOriginal.value], () => {
  if (!editDirty.value) loadEditText()
})

function onEditInput() {
  editDirty.value = true
}

function saveEdit() {
  const num = props.state.expandChapterNum.value
  if (!num || !editText.value) return
  // Also update the state so diff refreshes
  if (editTarget.value === 'new') {
    props.state.expandNew.value = editText.value
  } else {
    props.state.expandOriginal.value = editText.value
  }
  // Save to file (using the selected text)
  props.state.saveExpandResult(editTarget.value === 'new')
  editDirty.value = false
}
</script>

<template>
  <StepCard :step="5" title="场景润色" description="对章节进行深度润色，增强细节与氛围">
    <div class="space-y-3">
      <p class="text-sm text-[var(--color-ink-light)]">对第 <strong>{{ state.chapterNum.value }}</strong> 章进行场景润色（章节号与步骤3联动）。</p>
      <div>
        <label class="block text-xs text-[var(--color-ink-light)] mb-1">润色建议（可选）</label>
        <textarea v-model="state.polishGuidance.value" rows="3" placeholder="例如：加强环境描写、增加角色心理活动、丰富对话细节…" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm resize-y" />
      </div>
      <div class="flex justify-end">
        <button @click="state.doExpand()" :disabled="state.expand.value.running || !state.llmConfig.value" class="btn-primary" type="button">
          {{ state.expand.value.running ? '润色中…' : '▶ 场景润色' }}
        </button>
      </div>

      <!-- 运行中进度 -->
      <div v-if="state.expand.value.running" class="rounded-lg border border-[var(--color-parchment-darker)] bg-white">
        <div class="sticky top-0 z-10 text-xs px-3 py-1 flex items-center gap-2 bg-[var(--color-leather)] text-[var(--color-gold-light)] rounded-t-lg">
          <span class="inline-block w-2 h-2 rounded-full bg-[var(--color-gold)] animate-pulse" />
          <span class="italic flex-1">{{ state.expand.value.progress || '润色中...' }}</span>
          <div v-if="state.expand.value.progressValue !== undefined" class="w-24 h-1.5 bg-white/20 rounded-full overflow-hidden">
            <div class="h-full bg-[var(--color-gold)] rounded-full transition-all" :style="{ width: (state.expand.value.progressValue * 100) + '%' }" />
          </div>
          <button @click="state.cancelSSE(state.expand.value)"
            class="ml-2 px-2 py-0.5 rounded text-xs font-semibold bg-red-600 text-white hover:bg-red-700" type="button">停止</button>
        </div>
        <div v-if="state.expand.value.result" class="p-3 text-sm font-mono whitespace-pre-wrap text-[var(--color-ink-light)] max-h-40 overflow-y-auto">
          {{ state.expand.value.result.slice(0, 200) }}…
        </div>
      </div>

      <!-- 错误提示 -->
      <p v-if="state.expand.value.error" class="text-xs text-red-500">{{ state.expand.value.error }}</p>

      <!-- 润色结果 -->
      <div v-if="state.expandNew.value && !state.expand.value.running" class="space-y-3">

        <!-- ====== 对比面板（段落对齐） ====== -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-0 rounded-lg border border-[var(--color-parchment-darker)] overflow-hidden">
          <!-- 左列标题：新内容 -->
          <div class="px-3 py-2 bg-green-50 border-b border-r border-[var(--color-parchment-darker)] flex items-center justify-between">
            <span class="text-sm font-medium text-green-700">✨ 润色后（新）</span>
            <span class="text-xs text-[var(--color-ink-light)]">{{ state.expandNew.value.length }} 字</span>
          </div>
          <!-- 右列标题：旧内容 -->
          <div class="px-3 py-2 bg-amber-50 border-b border-[var(--color-parchment-darker)] flex items-center justify-between">
            <span class="text-sm font-medium text-amber-700">📄 润色前（旧）</span>
            <span class="text-xs text-[var(--color-ink-light)]">{{ state.expandOriginal.value.length }} 字</span>
          </div>
          <!-- 左列内容 -->
          <div
            ref="leftPanel"
            @scroll="onLeftScroll"
            class="diff-panel bg-white overflow-y-auto border-r border-[var(--color-parchment-darker)]"
            style="min-height: 400px; max-height: 600px"
          >
            <div v-for="(row, idx) in alignedRows" :key="'l'+idx"
              class="px-3 py-1.5 text-sm font-mono whitespace-pre-wrap border-b border-gray-100"
              :class="{
                'bg-green-50/50': row.type === 'added',
                'bg-amber-50/30': row.type === 'modified',
                'bg-gray-50 text-gray-300': row.type === 'removed',
              }"
            >
              <template v-if="row.type === 'equal'">{{ row.newPara }}</template>
              <template v-else-if="row.type === 'added'"><span class="diff-add" v-html="escapeHtml(row.newPara)" /></template>
              <template v-else-if="row.type === 'removed'"><span class="text-gray-300 italic text-xs">（无对应段落）</span></template>
              <template v-else><span v-html="charDiffHtml(row.oldPara, row.newPara, 'new')" /></template>
            </div>
          </div>
          <!-- 右列内容 -->
          <div
            ref="rightPanel"
            @scroll="onRightScroll"
            class="diff-panel bg-white overflow-y-auto"
            style="min-height: 400px; max-height: 600px"
          >
            <div v-for="(row, idx) in alignedRows" :key="'r'+idx"
              class="px-3 py-1.5 text-sm font-mono whitespace-pre-wrap border-b border-gray-100"
              :class="{
                'bg-red-50/50': row.type === 'removed',
                'bg-amber-50/30': row.type === 'modified',
                'bg-gray-50 text-gray-300': row.type === 'added',
              }"
            >
              <template v-if="row.type === 'equal'">{{ row.oldPara }}</template>
              <template v-else-if="row.type === 'removed'"><span class="diff-del" v-html="escapeHtml(row.oldPara)" /></template>
              <template v-else-if="row.type === 'added'"><span class="text-gray-300 italic text-xs">（无对应段落）</span></template>
              <template v-else><span v-html="charDiffHtml(row.oldPara, row.newPara, 'old')" /></template>
            </div>
          </div>
        </div>

        <!-- ====== 编辑面板 ====== -->
        <div class="rounded-lg border border-[var(--color-parchment-darker)] bg-white overflow-hidden">
          <div class="px-3 py-2 bg-gray-50 border-b border-[var(--color-parchment-darker)] flex items-center justify-between gap-3">
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-[var(--color-leather)]">✏️ 编辑</span>
              <select v-model="editTarget" class="border border-[var(--color-parchment-darker)] rounded px-2 py-1 text-sm">
                <option value="old">润色前（旧）</option>
                <option value="new">润色后（新）</option>
              </select>
              <span v-if="editDirty" class="text-xs text-amber-600">● 未保存</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-xs text-[var(--color-ink-light)]">{{ editText.length }} 字</span>
              <span v-if="state.saveMsg.value" class="text-xs" :class="state.saveMsg.value.startsWith('✅') ? 'text-green-600' : 'text-red-500'">{{ state.saveMsg.value }}</span>
              <button @click="loadEditText()" :disabled="!editDirty" class="btn-sm" type="button">↩ 撤销修改</button>
              <button @click="saveEdit()" :disabled="!editText"
                class="btn-sm bg-green-600 text-white hover:bg-green-700" type="button">
                💾 保存到第 {{ state.expandChapterNum.value }} 章
              </button>
            </div>
          </div>
          <textarea
            v-model="editText"
            @input="onEditInput"
            class="w-full border-0 px-3 py-2 text-sm font-mono resize-y focus:outline-none"
            style="min-height: 300px"
            placeholder="选择要编辑的版本…"
          />
        </div>

      </div>
    </div>
  </StepCard>
</template>

<style scoped>
.diff-panel :deep(.diff-add) {
  background-color: #bbf7d0;
  border-radius: 2px;
  padding: 0 1px;
}
.diff-panel :deep(.diff-del) {
  background-color: #fecaca;
  text-decoration: line-through;
  border-radius: 2px;
  padding: 0 1px;
  opacity: 0.7;
}
</style>
