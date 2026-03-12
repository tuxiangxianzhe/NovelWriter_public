<script setup lang="ts">
import type { useWorkshopState } from '@/composables/useWorkshopState'
import StepCard from '@/components/StepCard.vue'
import StreamOutput from '@/components/StreamOutput.vue'

defineProps<{ state: ReturnType<typeof useWorkshopState> }>()
</script>

<template>
  <StepCard :step="4" title="精炼章节（定稿）" description="对草稿进行润色、逻辑修正">
    <div class="space-y-3">
      <p class="text-sm text-[var(--color-ink-light)]">对第 <strong>{{ state.chapterNum.value }}</strong> 章进行精炼定稿（章节号与步骤3联动）。</p>
      <div class="flex justify-end">
        <button @click="state.doFinalize()" :disabled="state.finalize.value.running || !state.llmConfig.value || !state.embConfig.value" class="btn-primary" type="button">
          {{ state.finalize.value.running ? '精炼中…' : '▶ 精炼章节' }}
        </button>
      </div>
      <StreamOutput
        :progress="state.finalize.value.progress"
        :result="state.finalize.value.result"
        :error="state.finalize.value.error"
        :running="state.finalize.value.running"
        :progress-value="state.finalize.value.progressValue"
        :cancelable="true"
        placeholder="精炼结果将在此显示…"
        @cancel="state.cancelSSE(state.finalize.value)"
      />
    </div>
  </StepCard>
</template>
