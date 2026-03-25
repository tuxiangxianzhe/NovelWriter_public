<script setup lang="ts">
import { computed } from 'vue'
import type { useWorkshopState } from '@/composables/useWorkshopState'
import StepCard from '@/components/StepCard.vue'
import StreamOutput from '@/components/StreamOutput.vue'

const props = defineProps<{ state: ReturnType<typeof useWorkshopState> }>()

const previewContent = computed(() => {
  const tab = props.state.humanizerPreviewTab.value
  if (tab === 'original') return props.state.humanizerOriginal.value
  if (tab === 'changes') return props.state.humanizerChanges.value
  return props.state.humanizerHumanized.value
})
</script>

<template>
  <StepCard :step="6" title="去 AI 痕迹" description="清除章节中的 AI 生成痕迹，保留文学性和叙事节奏">
    <div class="space-y-3">
      <!-- 模式切换 -->
      <div class="flex items-center gap-4">
        <label class="flex items-center gap-1.5 text-sm">
          <input type="radio" :value="false" v-model="state.humanizerBatch.value" />
          单章处理
        </label>
        <label class="flex items-center gap-1.5 text-sm">
          <input type="radio" :value="true" v-model="state.humanizerBatch.value" />
          批量处理
        </label>
      </div>

      <!-- 单章模式 -->
      <div v-if="!state.humanizerBatch.value">
        <p class="text-sm text-[var(--color-ink-light)]">
          对第 <strong>{{ state.chapterNum.value }}</strong> 章去 AI 痕迹（章节号与步骤3联动）。
        </p>
      </div>

      <!-- 批量模式 -->
      <div v-else class="flex items-center gap-2">
        <label class="text-sm text-[var(--color-ink-light)]">章节范围：第</label>
        <input type="number" v-model.number="state.humanizerStart.value" min="1" class="w-16 border border-[var(--color-parchment-darker)] rounded px-2 py-1 text-sm text-center" />
        <span class="text-sm">~</span>
        <input type="number" v-model.number="state.humanizerEnd.value" min="1" class="w-16 border border-[var(--color-parchment-darker)] rounded px-2 py-1 text-sm text-center" />
        <label class="text-sm text-[var(--color-ink-light)]">章</label>
      </div>

      <!-- 处理深度 -->
      <div>
        <label class="block text-xs text-[var(--color-ink-light)] mb-1">处理深度</label>
        <div class="flex gap-2">
          <label
            v-for="opt in [
              { value: 'quick', label: '快速', desc: '1轮，R1-R7一次处理' },
              { value: 'standard', label: '标准', desc: '2轮，句式→词汇' },
              { value: 'deep', label: '深度', desc: '3轮，句式→词汇→节奏' },
            ]" :key="opt.value"
            class="flex-1 flex items-center gap-1.5 px-3 py-2 rounded-lg border cursor-pointer transition-colors text-sm"
            :class="state.humanizerDepth.value === opt.value
              ? 'bg-blue-50 border-blue-300 text-blue-700'
              : 'border-[var(--color-parchment-darker)] hover:border-blue-200'"
          >
            <input type="radio" :value="opt.value" v-model="state.humanizerDepth.value" class="sr-only" />
            <div>
              <span class="font-medium">{{ opt.label }}</span>
              <span class="text-xs text-[var(--color-ink-light)] ml-1">{{ opt.desc }}</span>
            </div>
          </label>
        </div>
      </div>

      <!-- R8 开关 -->
      <div class="flex items-start gap-2 p-3 rounded-md" style="background: var(--color-parchment-light)">
        <label class="flex items-center gap-1.5 text-sm font-medium shrink-0 mt-0.5">
          <input type="checkbox" v-model="state.humanizerR8.value" />
          R8 无用细节清除
        </label>
        <p class="text-xs text-[var(--color-ink-light)]">
          开启后会大幅削减原文细节描写，可能删除你认为重要的内容。需额外读取大纲/角色状态作为判断依据，消耗更多 token。
        </p>
      </div>

      <!-- 用户重点说明 -->
      <div>
        <label class="block text-xs text-[var(--color-ink-light)] mb-1">本章重点说明（可选，辅助 R8 判断）</label>
        <textarea v-model="state.humanizerFocus.value" rows="2" placeholder="例如：本章重点是男女主的矛盾爆发，战斗场景的细节不要删…" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm resize-y" />
      </div>

      <!-- 执行按钮 -->
      <div class="flex justify-end">
        <button
          @click="state.humanizerBatch.value ? state.doBatchHumanize() : state.doHumanize()"
          :disabled="state.humanize.value.running || !state.llmConfig.value"
          class="btn-primary" type="button"
        >
          {{ state.humanize.value.running ? '处理中…' : (state.humanizerBatch.value ? '▶ 批量去 AI' : '▶ 去 AI 痕迹') }}
        </button>
      </div>

      <!-- 进度显示（处理中） -->
      <div v-if="state.humanize.value.running || (!state.humanizerPending.value && (state.humanize.value.progress || state.humanize.value.error))">
        <StreamOutput
          :progress="state.humanize.value.progress"
          :result="state.humanizerPending.value ? '' : state.humanize.value.result"
          :error="state.humanize.value.error"
          :running="state.humanize.value.running"
          :progress-value="state.humanize.value.progressValue"
          :cancelable="true"
          placeholder="去 AI 结果将在此显示…"
          @cancel="state.cancelSSE(state.humanize.value)"
        />
      </div>

      <!-- 对比预览区（处理完成后，单章模式） -->
      <div v-if="state.humanizerPending.value && !state.humanizerBatch.value" class="space-y-2">
        <!-- 标签页 -->
        <div class="flex border-b border-[var(--color-parchment-darker)]">
          <button
            @click="state.humanizerPreviewTab.value = 'humanized'"
            :class="state.humanizerPreviewTab.value === 'humanized' ? 'border-b-2 border-blue-500 text-blue-600 font-medium' : 'text-[var(--color-ink-light)]'"
            class="px-4 py-2 text-sm transition-colors" type="button"
          >
            去 AI 后
          </button>
          <button
            @click="state.humanizerPreviewTab.value = 'original'"
            :class="state.humanizerPreviewTab.value === 'original' ? 'border-b-2 border-amber-500 text-amber-600 font-medium' : 'text-[var(--color-ink-light)]'"
            class="px-4 py-2 text-sm transition-colors" type="button"
          >
            原文
          </button>
          <button
            @click="state.humanizerPreviewTab.value = 'changes'"
            :class="state.humanizerPreviewTab.value === 'changes' ? 'border-b-2 border-green-500 text-green-600 font-medium' : 'text-[var(--color-ink-light)]'"
            class="px-4 py-2 text-sm transition-colors" type="button"
          >
            修改清单
          </button>
        </div>

        <!-- 内容区 -->
        <div class="border border-[var(--color-parchment-darker)] rounded-md p-4 max-h-[500px] overflow-y-auto bg-white">
          <pre class="whitespace-pre-wrap text-sm leading-relaxed" style="font-family: inherit">{{ previewContent }}</pre>
        </div>

        <!-- 确认按钮 -->
        <div class="flex items-center justify-between pt-2">
          <p class="text-xs text-[var(--color-ink-light)]">请对比后选择保留哪个版本，确认后将写入文件。</p>
          <div class="flex gap-2">
            <button
              @click="state.doConfirmHumanize(false)"
              :disabled="state.humanizerSaving.value"
              class="px-4 py-1.5 text-sm rounded-md border border-[var(--color-parchment-darker)] hover:bg-gray-50 disabled:opacity-50"
              type="button"
            >
              保留原文
            </button>
            <button
              @click="state.doConfirmHumanize(true)"
              :disabled="state.humanizerSaving.value"
              class="btn-primary"
              type="button"
            >
              {{ state.humanizerSaving.value ? '保存中…' : '采用去 AI 版本' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </StepCard>
</template>
