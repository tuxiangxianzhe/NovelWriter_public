<script setup lang="ts">
import type { useWorkshopState } from '@/composables/useWorkshopState'
import StepCard from '@/components/StepCard.vue'
import StreamOutput from '@/components/StreamOutput.vue'

defineProps<{ state: ReturnType<typeof useWorkshopState> }>()
</script>

<template>
  <StepCard :step="2" title="生成章节目录" description="基于架构生成详细章节蓝图">
    <div class="space-y-3">
      <div class="flex flex-wrap gap-3 items-center">
        <div>
          <label class="block text-xs text-[var(--color-ink-light)] mb-1">叙事DNA</label>
          <select v-model="state.bpStyle.value" class="border border-[var(--color-parchment-darker)] rounded-md px-3 py-1.5 text-sm">
            <option v-for="s in state.styleList.value" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
        <div class="flex-1" />
        <button @click="state.doGenerateBP()" :disabled="state.bp.value.running || !state.llmConfig.value" class="btn-primary" type="button">
          {{ state.bp.value.running ? '生成中…' : '▶ 生成目录' }}
        </button>
      </div>
      <StreamOutput
        :progress="state.bp.value.progress"
        :result="state.bp.value.result"
        :error="state.bp.value.error"
        :running="state.bp.value.running"
        :editable="true"
        :progress-value="state.bp.value.progressValue"
        :cancelable="true"
        placeholder="章节目录将在此显示…"
        @update:result="state.bp.value.result = $event"
        @cancel="state.cancelSSE(state.bp.value)"
      />
      <div v-if="!state.bp.value.running" class="flex justify-end">
        <button @click="state.saveBlueprint()" class="btn-primary" type="button">💾 保存蓝图</button>
      </div>
    </div>
  </StepCard>
</template>
