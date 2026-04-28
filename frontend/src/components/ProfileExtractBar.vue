<script setup lang="ts">
defineProps<{
  show: boolean
  preferences: string
  confirmMsg: string
}>()

defineEmits<{
  confirm: []
  dismiss: []
}>()
</script>

<template>
  <!-- 确认条 -->
  <Transition name="slide-up">
    <div v-if="show"
      class="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 space-y-2">
      <div class="flex items-start gap-2">
        <span class="text-amber-600 text-sm font-medium shrink-0">💡 检测到偏好：</span>
        <pre class="text-sm text-[var(--color-ink)] whitespace-pre-wrap flex-1">{{ preferences }}</pre>
      </div>
      <div class="flex items-center justify-end gap-2">
        <button @click="$emit('dismiss')"
          class="px-3 py-1 rounded text-xs text-[var(--color-ink-light)] hover:bg-gray-100" type="button">
          忽略
        </button>
        <button @click="$emit('confirm')"
          class="px-3 py-1 rounded text-xs bg-amber-500 text-white hover:bg-amber-600" type="button">
          加入画像
        </button>
      </div>
    </div>
  </Transition>
  <!-- 结果提示 -->
  <span v-if="confirmMsg" class="text-xs" :class="confirmMsg.startsWith('✅') ? 'text-green-600' : 'text-red-500'">
    {{ confirmMsg }}
  </span>
</template>

<style scoped>
.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.2s ease;
}
.slide-up-enter-from, .slide-up-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
