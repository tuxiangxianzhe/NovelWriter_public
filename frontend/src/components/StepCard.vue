<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  step: number | string
  title: string
  description?: string
  collapsible?: boolean
  defaultOpen?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  description: '',
  collapsible: true,
  defaultOpen: true,
})

const open = ref(props.defaultOpen)
</script>

<template>
  <div class="rounded-xl shadow-md border border-[var(--color-parchment-darker)] bg-white overflow-hidden">
    <!-- 头部 -->
    <button
      v-if="collapsible"
      class="w-full flex items-center gap-3 px-5 py-4 text-left transition-colors hover:bg-[var(--color-parchment)]"
      :class="open ? 'bg-[var(--color-parchment)]' : 'bg-white'"
      @click="open = !open"
      type="button"
    >
      <!-- 步骤徽章 -->
      <span
        class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold text-[var(--color-parchment)]"
        style="background-color: var(--color-gold-dark)"
      >
        {{ step }}
      </span>
      <div class="flex-1 min-w-0">
        <h3 class="font-semibold text-[var(--color-ink)] truncate">{{ title }}</h3>
        <p v-if="description" class="text-xs text-[var(--color-ink-light)] mt-0.5 line-clamp-1">
          {{ description }}
        </p>
      </div>
      <!-- 展开/收起箭头 -->
      <svg
        class="flex-shrink-0 w-4 h-4 text-[var(--color-leather)] transition-transform"
        :class="open ? 'rotate-180' : ''"
        fill="none" stroke="currentColor" viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <!-- 非折叠头部 -->
    <div
      v-else
      class="flex items-center gap-3 px-5 py-4 bg-[var(--color-parchment)]"
    >
      <span
        class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold text-[var(--color-parchment)]"
        style="background-color: var(--color-gold-dark)"
      >
        {{ step }}
      </span>
      <div>
        <h3 class="font-semibold text-[var(--color-ink)]">{{ title }}</h3>
        <p v-if="description" class="text-xs text-[var(--color-ink-light)] mt-0.5">{{ description }}</p>
      </div>
    </div>

    <!-- 内容区 -->
    <Transition name="slide">
      <div v-if="!collapsible || open" class="px-5 py-4 border-t border-[var(--color-parchment-darker)]">
        <slot />
      </div>
    </Transition>
  </div>
</template>
