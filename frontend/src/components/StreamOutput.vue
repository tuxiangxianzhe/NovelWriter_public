<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue'

interface Props {
  progress?: string
  result?: string
  error?: string
  running?: boolean
  placeholder?: string
  editable?: boolean
  progressValue?: number
  cancelable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  progress: '',
  result: '',
  error: '',
  running: false,
  placeholder: '等待生成...',
  editable: false,
  progressValue: undefined,
  cancelable: false,
})

const emit = defineEmits<{
  (e: 'update:result', v: string): void
  (e: 'cancel'): void
}>()

const containerRef = ref<HTMLElement>()
const hasEdited = ref(false)

function onEdit(event: Event) {
  hasEdited.value = true
  emit('update:result', (event.target as HTMLTextAreaElement).value)
}

// 警告检测：⚠️ 开头的 progress 消息视为持久警告
const warning = ref('')
watch(
  () => props.progress,
  (msg) => {
    if (msg && msg.startsWith('⚠️')) {
      warning.value = msg
    }
  },
)
// running 变为 false 时不清除 warning，保持持久显示
// 新的 running 周期开始时清除旧警告
watch(
  () => props.running,
  (running) => {
    if (running) {
      warning.value = ''
      hasEdited.value = false
    }
  },
)
// 加载已有内容时标记为已编辑，防止清空后 textarea 消失
watch(
  () => props.result,
  (val) => {
    if (val && props.editable) hasEdited.value = true
  },
  { immediate: true },
)

const isWarning = computed(() => !!warning.value)
const progressPercent = computed(() => {
  if (props.progressValue === undefined || props.progressValue === null) return null
  return Math.round(props.progressValue * 100)
})

watch(
  () => [props.progress, props.result],
  async () => {
    await nextTick()
    if (containerRef.value) {
      containerRef.value.scrollTop = containerRef.value.scrollHeight
    }
  },
)
</script>

<template>
  <div
    ref="containerRef"
    class="relative rounded-lg border border-[var(--color-parchment-darker)] bg-[var(--color-spine)] text-[var(--color-parchment)] font-mono text-sm overflow-y-auto"
    style="min-height: 160px; max-height: 70vh"
  >
    <!-- 运行指示条 -->
    <div
      v-if="running"
      class="sticky top-0 z-10 text-xs px-3 py-1 flex items-center gap-2"
      :class="isWarning ? 'bg-amber-700 text-amber-100' : 'bg-[var(--color-leather)] text-[var(--color-gold-light)]'"
    >
      <span class="inline-block w-2 h-2 rounded-full animate-pulse" :class="isWarning ? 'bg-amber-300' : 'bg-[var(--color-gold)]'" />
      <span class="italic flex-1">{{ progress || '生成中...' }}</span>
      <span v-if="progressPercent !== null" class="font-mono tabular-nums">{{ progressPercent }}%</span>
      <button
        v-if="cancelable"
        @click="emit('cancel')"
        class="ml-2 px-2 py-0.5 rounded text-xs font-semibold bg-red-600 text-white hover:bg-red-700 transition-colors"
        type="button"
      >
        停止
      </button>
    </div>

    <!-- 进度条 -->
    <div v-if="running && progressPercent !== null" class="h-1 bg-[var(--color-parchment-darker)]">
      <div
        class="h-full transition-all duration-300 ease-out"
        :class="isWarning ? 'bg-amber-500' : 'bg-[var(--color-gold)]'"
        :style="{ width: progressPercent + '%' }"
      />
    </div>

    <!-- 持久警告条 -->
    <div
      v-if="warning"
      class="px-3 py-1.5 text-xs bg-amber-100 text-amber-800 border-b border-amber-300"
    >
      {{ warning }}
    </div>

    <div class="p-3">
      <!-- 错误 -->
      <p v-if="error" class="text-red-400 whitespace-pre-wrap mb-2">{{ error }}</p>

      <!-- 结果：可编辑模式始终显示 textarea -->
      <textarea
        v-if="editable && (result || hasEdited)"
        :value="result"
        @input="onEdit($event)"
        class="w-full bg-transparent text-[var(--color-parchment)] resize-none outline-none whitespace-pre-wrap leading-relaxed"
        style="min-height: 300px"
        :placeholder="placeholder"
      />
      <!-- 结果：只读模式 -->
      <pre v-else-if="result && !editable" class="whitespace-pre-wrap leading-relaxed text-[var(--color-parchment-dark)]">{{ result }}</pre>

      <!-- 占位符 -->
      <p
        v-else-if="!running && !error"
        class="text-[var(--color-ink-light)] italic opacity-50"
      >
        {{ placeholder }}
      </p>
    </div>
  </div>
</template>
