<script setup lang="ts">
import type { useWorkshopState } from '@/composables/useWorkshopState'
import StepCard from '@/components/StepCard.vue'
import StreamOutput from '@/components/StreamOutput.vue'

defineProps<{ state: ReturnType<typeof useWorkshopState> }>()
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
      <StreamOutput
        :progress="state.expand.value.progress"
        :result="state.expand.value.result"
        :error="state.expand.value.error"
        :running="state.expand.value.running"
        :editable="true"
        :progress-value="state.expand.value.progressValue"
        :cancelable="true"
        placeholder="润色结果将在此显示…"
        @update:result="state.expand.value.result = $event"
        @cancel="state.cancelSSE(state.expand.value)"
      />
    </div>
  </StepCard>
</template>
