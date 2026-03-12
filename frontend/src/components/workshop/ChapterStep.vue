<script setup lang="ts">
import type { useWorkshopState } from '@/composables/useWorkshopState'
import StepCard from '@/components/StepCard.vue'
import StreamOutput from '@/components/StreamOutput.vue'

defineProps<{ state: ReturnType<typeof useWorkshopState> }>()
</script>

<template>
  <StepCard :step="3" title="生成章节草稿" description="根据蓝图逐章生成正文">
    <div class="space-y-3">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        <div>
          <label class="block text-xs text-[var(--color-ink-light)] mb-1">章节号</label>
          <input v-model.number="state.chapterNum.value" type="number" min="1" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
        </div>
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
        <div>
          <label class="block text-xs text-[var(--color-ink-light)] mb-1">涉及人物</label>
          <input v-model="state.charactersInvolved.value" placeholder="可选" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
        </div>
        <div>
          <label class="block text-xs text-[var(--color-ink-light)] mb-1">关键物品</label>
          <input v-model="state.keyItems.value" placeholder="可选" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
        </div>
        <div>
          <label class="block text-xs text-[var(--color-ink-light)] mb-1">场景地点</label>
          <input v-model="state.sceneLocation.value" placeholder="可选" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
        </div>
        <div>
          <label class="block text-xs text-[var(--color-ink-light)] mb-1">时间约束</label>
          <input v-model="state.timeConstraint.value" placeholder="可选" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
        </div>
        <div class="sm:col-span-2">
          <label class="block text-xs text-[var(--color-ink-light)] mb-1">章节指导（覆盖全局）</label>
          <input v-model="state.chGuidance.value" placeholder="可选" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
        </div>
        <div class="flex items-center gap-2">
          <input id="inject-world" v-model="state.injectWorldBuilding.value" type="checkbox" class="rounded border-[var(--color-parchment-darker)]" />
          <label for="inject-world" class="text-xs text-[var(--color-ink-light)] select-none">注入世界观设定</label>
        </div>
      </div>
      <div class="flex justify-end">
        <button @click="state.doGenerateChapter()" :disabled="state.chapter.value.running || !state.llmConfig.value || !state.embConfig.value" class="btn-primary" type="button">
          {{ state.chapter.value.running ? '生成中…' : '▶ 生成章节' }}
        </button>
      </div>
      <StreamOutput
        :progress="state.chapter.value.progress"
        :result="state.chapter.value.result"
        :error="state.chapter.value.error"
        :running="state.chapter.value.running"
        :editable="true"
        :progress-value="state.chapter.value.progressValue"
        :cancelable="true"
        placeholder="章节内容将在此显示…"
        @update:result="state.chapter.value.result = $event"
        @cancel="state.cancelSSE(state.chapter.value)"
      />
      <div v-if="state.chapter.value.result && !state.chapter.value.running" class="flex justify-end">
        <button @click="state.saveChapter()" class="btn-primary" type="button">💾 保存章节</button>
      </div>
    </div>
  </StepCard>
</template>
