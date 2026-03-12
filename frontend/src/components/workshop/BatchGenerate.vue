<script setup lang="ts">
import type { useWorkshopState } from '@/composables/useWorkshopState'
import StreamOutput from '@/components/StreamOutput.vue'

defineProps<{ state: ReturnType<typeof useWorkshopState> }>()
</script>

<template>
  <div class="rounded-xl border border-[var(--color-parchment-darker)] bg-white p-5 space-y-3">
    <div class="flex items-center justify-between">
      <div>
        <h3 class="font-semibold text-[var(--color-leather)]">一键完成小说</h3>
        <p class="text-xs text-[var(--color-ink-light)]">自动逐章生成草稿并定稿，完成后自动合并导出。支持断点续传（已有章节自动跳过）。使用步骤3中所选的文风与叙事DNA。</p>
      </div>
      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2">
          <input id="batch-inject-world" v-model="state.injectWorldBuilding.value" type="checkbox" class="rounded border-[var(--color-parchment-darker)]" />
          <label for="batch-inject-world" class="text-xs text-[var(--color-ink-light)] select-none whitespace-nowrap">注入世界观</label>
        </div>
        <button @click="state.doBatchGenerate()" :disabled="state.batch.value.running || !state.llmConfig.value || !state.embConfig.value" class="btn-primary" type="button">
          {{ state.batch.value.running ? '批量生成中…' : '▶ 一键完成小说' }}
        </button>
      </div>
    </div>
    <StreamOutput
      :progress="state.batch.value.progress"
      :result="state.batch.value.result"
      :error="state.batch.value.error"
      :running="state.batch.value.running"
      :progress-value="state.batch.value.progressValue"
      :cancelable="true"
      placeholder="批量生成进度将在此显示…"
      @cancel="state.cancelSSE(state.batch.value)"
    />
  </div>
</template>
