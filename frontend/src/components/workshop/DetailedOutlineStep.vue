<script setup lang="ts">
import { ref } from 'vue'
import type { useWorkshopState } from '@/composables/useWorkshopState'
import StepCard from '@/components/StepCard.vue'

const props = defineProps<{ state: ReturnType<typeof useWorkshopState> }>()

const extractChapterNum = ref<number | null>(null)
const extractMsg = ref('')

function doExtract() {
  if (!extractChapterNum.value || extractChapterNum.value < 1) return
  extractMsg.value = ''
  props.state.extractChapterToEdit(extractChapterNum.value)
  if (props.state.outlineBatchResult.value) {
    extractMsg.value = `✅ 第${extractChapterNum.value}章已抽取到上方编辑区`
  } else {
    extractMsg.value = `❌ 未找到第${extractChapterNum.value}章细纲`
  }
  setTimeout(() => { extractMsg.value = '' }, 4000)
}
</script>

<template>
  <StepCard :step="'2.5'" title="生成章节细纲" description="场景分解、节奏曲线、对话要点 — 在蓝图和正文之间的精细控制层">
    <div class="space-y-3">
      <!-- 细纲模式 -->
      <div class="flex items-center gap-2">
        <span class="text-xs text-[var(--color-ink-light)]">细纲模式：</span>
        <button @click="state.outlineMode.value = 'concise'"
          class="px-2.5 py-1 rounded text-xs transition-colors"
          :class="state.outlineMode.value === 'concise'
            ? 'bg-[var(--color-leather)] text-[var(--color-parchment)]'
            : 'bg-[var(--color-parchment-dark)] text-[var(--color-ink-light)] hover:bg-[var(--color-parchment-darker)]'"
          type="button">精简（1000-2000字/章）</button>
        <button @click="state.outlineMode.value = 'detailed'"
          class="px-2.5 py-1 rounded text-xs transition-colors"
          :class="state.outlineMode.value === 'detailed'
            ? 'bg-[var(--color-leather)] text-[var(--color-parchment)]'
            : 'bg-[var(--color-parchment-dark)] text-[var(--color-ink-light)] hover:bg-[var(--color-parchment-darker)]'"
          type="button">详细（3000-5000字/章）</button>
        <span class="text-xs text-[var(--color-ink-light)] italic">
          {{ state.outlineMode.value === 'detailed' ? '适合官能占比高的剧情，包含感官/心理/阶段推进细节' : '骨架式细纲，场景事件概括 + 行为要点' }}
        </span>
      </div>

      <!-- 批次控制 -->
      <div class="flex flex-wrap gap-3 items-end">
        <div>
          <label class="block text-xs text-[var(--color-ink-light)] mb-1">起始章节</label>
          <input v-model.number="state.outlineBatchStart.value" type="number" min="1"
            class="w-24 border border-[var(--color-parchment-darker)] rounded-md px-3 py-1.5 text-sm" />
        </div>
        <div>
          <label class="block text-xs text-[var(--color-ink-light)] mb-1">每批章数</label>
          <input v-model.number="state.outlineBatchSize.value" type="number" min="1" max="10"
            class="w-24 border border-[var(--color-parchment-darker)] rounded-md px-3 py-1.5 text-sm" />
        </div>
        <div class="flex-1 text-xs text-[var(--color-ink-light)] self-center">
          将生成第 {{ state.outlineBatchStart.value }} - {{ Math.min(state.outlineBatchStart.value + state.outlineBatchSize.value - 1, state.numChapters.value) }} 章的细纲
          （共 {{ state.numChapters.value }} 章）
        </div>
        <button
          @click="state.doGenerateOutlineBatch()"
          :disabled="state.detailedOutline.value.running || !state.llmConfig.value || state.outlineBatchStart.value > state.numChapters.value"
          class="btn-primary"
          type="button"
        >
          {{ state.detailedOutline.value.running ? '生成中…' : `▶ 生成第${state.outlineBatchStart.value}-${Math.min(state.outlineBatchStart.value + state.outlineBatchSize.value - 1, state.numChapters.value)}章细纲` }}
        </button>
      </div>

      <!-- 当前批次结果（始终可编辑） -->
      <div class="relative rounded-lg border border-[var(--color-parchment-darker)] bg-white">
        <!-- 运行状态条 -->
        <div v-if="state.detailedOutline.value.running"
          class="sticky top-0 z-10 text-xs px-3 py-1 flex items-center gap-2 bg-[var(--color-leather)] text-[var(--color-gold-light)] rounded-t-lg">
          <span class="inline-block w-2 h-2 rounded-full bg-[var(--color-gold)] animate-pulse" />
          <span class="italic flex-1">{{ state.detailedOutline.value.progress || '生成中...' }}</span>
          <button @click="state.cancelSSE(state.detailedOutline.value)"
            class="ml-2 px-2 py-0.5 rounded text-xs font-semibold bg-red-600 text-white hover:bg-red-700" type="button">停止</button>
        </div>
        <textarea
          v-model="state.outlineBatchResult.value"
          rows="12"
          :disabled="state.detailedOutline.value.running"
          class="w-full border-0 rounded-lg px-3 py-2 text-sm font-mono resize-y disabled:opacity-60"
          style="min-height: 200px"
          placeholder="点击上方按钮生成当前批次的章节细纲，也可直接手动输入或粘贴…"
        />
        <p v-if="state.detailedOutline.value.error" class="px-3 pb-2 text-xs text-red-500">{{ state.detailedOutline.value.error }}</p>
      </div>

      <!-- 当前批次操作：保存 + 修订 -->
      <div v-if="state.outlineBatchResult.value && !state.detailedOutline.value.running" class="space-y-2">
        <div class="flex justify-end">
          <button @click="state.saveBatchOutline()" class="btn-sm" type="button">
            💾 确认本批细纲并保存
          </button>
        </div>

        <!-- 修订面板 -->
        <details class="border border-dashed border-[var(--color-parchment-darker)] rounded-lg">
          <summary class="px-3 py-2 cursor-pointer text-xs font-medium text-[var(--color-leather)] select-none">✏️ 基于建议修订本批细纲</summary>
          <div class="px-3 pb-3 pt-1 space-y-2">
            <div class="flex flex-wrap gap-x-3 gap-y-1 text-xs text-[var(--color-ink-light)]">
              <span>注入上下文：</span>
              <label class="inline-flex items-center gap-1 cursor-pointer"><input type="checkbox" v-model="state.revisionContext.value.include_core_seed" class="rounded" />种子</label>
              <label class="inline-flex items-center gap-1 cursor-pointer"><input type="checkbox" v-model="state.revisionContext.value.include_characters" class="rounded" />角色</label>
              <label class="inline-flex items-center gap-1 cursor-pointer"><input type="checkbox" v-model="state.revisionContext.value.include_world_building" class="rounded" />世界观</label>
              <label class="inline-flex items-center gap-1 cursor-pointer"><input type="checkbox" v-model="state.revisionContext.value.include_plot" class="rounded" />剧情</label>
            </div>
            <input v-model="state.outlineRevisionGuidance.value" placeholder="输入修改建议，如：第3章的官能场景需要更详细的阶段规划、第5章节奏太平…"
              class="w-full border border-[var(--color-parchment-darker)] rounded px-2 py-1 text-sm" />
            <div class="flex items-center gap-2">
              <button @click="state.doReviseOutlineBatch()"
                :disabled="state.outlineRevision.value.running || !state.outlineRevisionGuidance.value || !state.llmConfig.value"
                class="btn-sm" type="button">
                {{ state.outlineRevision.value.running ? '修订中…' : '▶ 修订' }}
              </button>
              <button v-if="state.outlineBatchBackup.value && !state.outlineRevision.value.running"
                @click="state.revertOutlineBatch()"
                class="btn-sm" type="button"
                title="回退到修订前的版本">
                ↩ 回退
              </button>
              <span v-if="state.outlineRevision.value.progress" class="text-xs text-[var(--color-ink-light)] italic">{{ state.outlineRevision.value.progress }}</span>
              <span v-if="state.outlineRevision.value.error" class="text-xs text-red-500">{{ state.outlineRevision.value.error }}</span>
            </div>
          </div>
        </details>
      </div>

      <!-- 完整细纲编辑区（始终可见，支持手动输入） -->
      <details class="border border-[var(--color-parchment-darker)] rounded-lg">
        <summary class="px-4 py-2 cursor-pointer text-sm font-medium text-[var(--color-leather)] select-none">
          完整细纲（可编辑 / 手动输入）
        </summary>
        <div class="px-4 pb-4 pt-2 space-y-2">
          <!-- 抽取章节到批次编辑区 -->
          <div v-if="state.outlineText.value" class="flex items-center gap-2 p-2 bg-[var(--color-parchment)] rounded-lg text-sm">
            <span class="text-xs text-[var(--color-ink-light)] whitespace-nowrap">抽取章节到上方编辑区：</span>
            <input v-model.number="extractChapterNum" type="number" min="1"
              class="w-20 border border-[var(--color-parchment-darker)] rounded px-2 py-1 text-sm" placeholder="章节号" />
            <button @click="doExtract" :disabled="!extractChapterNum || extractChapterNum < 1"
              class="btn-sm whitespace-nowrap" type="button">
              📤 抽取第{{ extractChapterNum || '?' }}章
            </button>
            <span v-if="extractMsg" class="text-xs" :class="extractMsg.startsWith('✅') ? 'text-green-600' : 'text-red-500'">{{ extractMsg }}</span>
          </div>
          <textarea
            v-model="state.outlineText.value"
            rows="20"
            class="w-full border border-[var(--color-parchment-darker)] rounded px-3 py-2 text-sm font-mono resize-y"
            style="min-height: 300px"
            placeholder="可直接手动输入或粘贴细纲内容，格式：【第1章细纲】标题\n场景分解：\n  场景1…"
          />
          <div class="flex justify-end">
            <button @click="state.saveOutline()" :disabled="!state.outlineText.value" class="btn-sm" type="button">
              💾 保存完整细纲
            </button>
          </div>
        </div>
      </details>
    </div>
  </StepCard>
</template>
