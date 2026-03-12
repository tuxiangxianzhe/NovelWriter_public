<script setup lang="ts">
import type { useWorkshopState } from '@/composables/useWorkshopState'

defineProps<{ state: ReturnType<typeof useWorkshopState> }>()
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
      <div class="sm:col-span-2">
        <label class="block text-xs text-[var(--color-ink-light)] mb-1">XP类型/核心玩法（可选）</label>
        <input v-model="state.xpType.value" placeholder="可留空" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
      </div>
      <div class="sm:col-span-2">
        <label class="block text-xs text-[var(--color-ink-light)] mb-1">全局创作指导</label>
        <textarea v-model="state.userGuidance.value" rows="3" placeholder="整体写作风格、重点注意事项…" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm resize-y" />
      </div>
    </div>
  </div>
</template>
