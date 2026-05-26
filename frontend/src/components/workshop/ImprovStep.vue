<script setup lang="ts">
import { ref, watch } from 'vue'
import type { useWorkshopState } from '@/composables/useWorkshopState'
import StepCard from '@/components/StepCard.vue'
import StreamOutput from '@/components/StreamOutput.vue'

const props = defineProps<{ state: ReturnType<typeof useWorkshopState> }>()

// 章节号变化时·重新加载已保存的本章蓝图/细纲
watch(() => props.state.chapterNum.value, () => {
  if (props.state.workflowMode.value === 'improv') {
    props.state.loadImprovBlueprint()
    props.state.loadImprovOutline()
  }
})

const showOpenThreads = ref(false)
const showOutline = ref(false)
</script>

<template>
  <div class="space-y-4">
    <!-- 单章蓝图 -->
    <StepCard :step="2" title="单章蓝图（即兴）" description="作者口述本章意图 → 生成单章蓝图">
      <div class="space-y-3">
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label class="block text-xs text-[var(--color-ink-light)] mb-1">章节号</label>
            <input v-model.number="state.chapterNum.value" type="number" min="1" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
          </div>
          <div class="sm:col-span-2">
            <label class="block text-xs text-[var(--color-ink-light)] mb-1">每章字数（基础值）</label>
            <input v-model.number="state.wordNumber.value" type="number" min="1000" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
          </div>
        </div>
        <div>
          <label class="block text-xs text-[var(--color-ink-light)] mb-1">
            本章意图（自由文本·可写一句话/半结构化/手写蓝图直接跳过生成）
          </label>
          <textarea
            v-model="state.improvIntent.value"
            rows="4"
            placeholder="例：本章想让主角与反派在城门口正面冲突，揭穿对方身份并埋下后续逃亡的伏笔……"
            class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm resize-y"
          />
        </div>
        <div class="flex justify-end gap-2">
          <button @click="state.loadImprovBlueprint()" class="btn-primary text-sm" type="button">🔄 重载</button>
          <button @click="state.doGenerateImprovBlueprint()" :disabled="state.improvBlueprint.value.running || !state.llmConfig.value" class="btn-primary" type="button">
            {{ state.improvBlueprint.value.running ? '生成中…' : '▶ 生成单章蓝图' }}
          </button>
        </div>
        <StreamOutput
          :progress="state.improvBlueprint.value.progress"
          :result="state.improvBlueprint.value.result || state.improvBlueprintText.value"
          :error="state.improvBlueprint.value.error"
          :running="state.improvBlueprint.value.running"
          :editable="true"
          :progress-value="state.improvBlueprint.value.progressValue"
          :cancelable="true"
          placeholder="单章蓝图将在此显示…"
          @update:result="state.improvBlueprint.value.result = $event"
          @cancel="state.cancelSSE(state.improvBlueprint.value)"
        />
        <div v-if="!state.improvBlueprint.value.running" class="flex justify-end">
          <button @click="state.saveImprovBlueprint()" class="btn-primary" type="button">💾 保存本章蓝图</button>
        </div>

        <!-- 修订面板 -->
        <details v-if="state.improvBlueprint.value.result || state.improvBlueprintText.value" class="border border-dashed border-[var(--color-parchment-darker)] rounded-lg">
          <summary class="px-3 py-2 cursor-pointer text-xs font-medium text-[var(--color-leather)] select-none">
            ✏️ 基于建议修订（仅调整指出的字段，其他保留）
          </summary>
          <div class="px-3 pb-3 pt-1 space-y-2">
            <textarea
              v-model="state.improvBlueprintRevisionGuidance.value"
              rows="3"
              placeholder="例：把章节强度改成★★★★★／核心冲突换成对峙而非追逐／结尾留更明显悬念…"
              class="w-full border border-[var(--color-parchment-darker)] rounded px-2 py-1.5 text-sm resize-y"
            />
            <div class="flex items-center justify-between">
              <span v-if="state.improvBlueprintRevise.value.progress" class="text-xs text-[var(--color-ink-light)] italic">{{ state.improvBlueprintRevise.value.progress }}</span>
              <span v-if="state.improvBlueprintRevise.value.error" class="text-xs text-red-500">{{ state.improvBlueprintRevise.value.error }}</span>
              <div class="flex-1" />
              <button
                @click="state.doReviseImprovBlueprint()"
                :disabled="state.improvBlueprintRevise.value.running || !state.improvBlueprintRevisionGuidance.value.trim() || !state.llmConfig.value"
                class="btn-primary text-sm"
                type="button"
              >
                {{ state.improvBlueprintRevise.value.running ? '修订中…' : '▶ 修订蓝图' }}
              </button>
            </div>
          </div>
        </details>
      </div>
    </StepCard>

    <!-- 单章细纲（可选） -->
    <StepCard :step="3" title="单章细纲（可选）" description="把蓝图展开成分场+对话钩子，仅在需要更精细控制时使用">
      <div class="space-y-3">
        <div class="flex justify-between items-center">
          <button @click="showOutline = !showOutline" class="text-sm text-blue-600 hover:text-blue-800" type="button">
            {{ showOutline ? '▼ 收起细纲面板' : '▶ 展开细纲面板（默认跳过）' }}
          </button>
          <div v-if="showOutline" class="flex gap-2">
            <button @click="state.loadImprovOutline()" class="btn-primary text-sm" type="button">🔄 重载</button>
            <button @click="state.doGenerateImprovOutline()" :disabled="state.improvOutline.value.running || !state.llmConfig.value" class="btn-primary" type="button">
              {{ state.improvOutline.value.running ? '生成中…' : '▶ 生成单章细纲' }}
            </button>
          </div>
        </div>
        <div v-if="showOutline" class="space-y-3">
          <StreamOutput
            :progress="state.improvOutline.value.progress"
            :result="state.improvOutline.value.result || state.improvOutlineText.value"
            :error="state.improvOutline.value.error"
            :running="state.improvOutline.value.running"
            :editable="true"
            :progress-value="state.improvOutline.value.progressValue"
            :cancelable="true"
            placeholder="单章细纲将在此显示…"
            @update:result="state.improvOutline.value.result = $event"
            @cancel="state.cancelSSE(state.improvOutline.value)"
          />
          <div v-if="!state.improvOutline.value.running" class="flex justify-end">
            <button @click="state.saveImprovOutline()" class="btn-primary" type="button">💾 保存本章细纲</button>
          </div>

          <!-- 修订面板 -->
          <details v-if="state.improvOutline.value.result || state.improvOutlineText.value" class="border border-dashed border-[var(--color-parchment-darker)] rounded-lg">
            <summary class="px-3 py-2 cursor-pointer text-xs font-medium text-[var(--color-leather)] select-none">
              ✏️ 基于建议修订（不偏离蓝图，仅调整分场细节）
            </summary>
            <div class="px-3 pb-3 pt-1 space-y-2">
              <textarea
                v-model="state.improvOutlineRevisionGuidance.value"
                rows="3"
                placeholder="例：场景 2 改在码头／加一段过渡场景／调整高潮的对话节奏／强化某段心理描写…"
                class="w-full border border-[var(--color-parchment-darker)] rounded px-2 py-1.5 text-sm resize-y"
              />
              <div class="flex items-center justify-between">
                <span v-if="state.improvOutlineRevise.value.progress" class="text-xs text-[var(--color-ink-light)] italic">{{ state.improvOutlineRevise.value.progress }}</span>
                <span v-if="state.improvOutlineRevise.value.error" class="text-xs text-red-500">{{ state.improvOutlineRevise.value.error }}</span>
                <div class="flex-1" />
                <button
                  @click="state.doReviseImprovOutline()"
                  :disabled="state.improvOutlineRevise.value.running || !state.improvOutlineRevisionGuidance.value.trim() || !state.llmConfig.value"
                  class="btn-primary text-sm"
                  type="button"
                >
                  {{ state.improvOutlineRevise.value.running ? '修订中…' : '▶ 修订细纲' }}
                </button>
              </div>
            </div>
          </details>
        </div>
      </div>
    </StepCard>

    <!-- 章节正文 -->
    <StepCard :step="4" title="章节正文（即兴）" description="基于已保存的单章蓝图（与可选细纲）生成正文">
      <div class="space-y-3">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="block text-xs text-[var(--color-ink-light)] mb-1">文风（文笔层）</label>
            <select v-model="state.chStyle.value" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm">
              <option v-for="s in state.styleList.value" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs text-[var(--color-ink-light)] mb-1">叙事DNA（叙事层）</label>
            <select v-model="state.chNarrativeStyle.value" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm">
              <option v-for="s in state.styleList.value" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div class="sm:col-span-2">
            <label class="block text-xs text-[var(--color-ink-light)] mb-1">章节指导（覆盖全局）</label>
            <input v-model="state.chGuidance.value" placeholder="可选" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
          </div>
        </div>
        <div class="flex justify-end">
          <button @click="state.doGenerateImprovChapter()" :disabled="state.improvChapter.value.running || !state.llmConfig.value" class="btn-primary" type="button">
            {{ state.improvChapter.value.running ? '生成中…' : '▶ 生成章节正文' }}
          </button>
        </div>
        <StreamOutput
          :progress="state.improvChapter.value.progress"
          :result="state.improvChapter.value.result"
          :error="state.improvChapter.value.error"
          :running="state.improvChapter.value.running"
          :editable="true"
          :progress-value="state.improvChapter.value.progressValue"
          :cancelable="true"
          placeholder="章节正文将在此显示…"
          @update:result="state.improvChapter.value.result = $event"
          @cancel="state.cancelSSE(state.improvChapter.value)"
        />
        <div v-if="state.improvChapter.value.result && !state.improvChapter.value.running" class="flex justify-end">
          <button @click="state.saveImprovChapter()" class="btn-primary" type="button">💾 保存章节</button>
        </div>
      </div>
    </StepCard>

    <!-- 伏笔池（open_threads） -->
    <StepCard :step="5" title="伏笔池（open_threads）" description="即兴模式连续性的核心。finalize 后自动更新；可手动编辑">
      <div class="space-y-3">
        <button @click="showOpenThreads = !showOpenThreads" class="text-sm text-blue-600 hover:text-blue-800" type="button">
          {{ showOpenThreads ? '▼ 收起伏笔池' : '▶ 展开伏笔池' }}
        </button>
        <div v-if="showOpenThreads" class="space-y-3">
          <textarea
            v-model="state.openThreadsText.value"
            rows="14"
            placeholder="伏笔池为空，写第 1 章 finalize 后会自动初始化…"
            class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm font-mono resize-y"
          />
          <div class="flex justify-end gap-2">
            <button @click="state.loadOpenThreads()" class="btn-primary text-sm" type="button">🔄 重载</button>
            <button @click="state.saveOpenThreadsText()" class="btn-primary" type="button">💾 保存伏笔池</button>
          </div>
        </div>
      </div>
    </StepCard>
  </div>
</template>
