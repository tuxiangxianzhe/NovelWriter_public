<script setup lang="ts">
import { ref, nextTick, onMounted, computed } from 'vue'
import { postSSE } from '@/api/client'
import { brainstormApi } from '@/api/client'
import { useConfigStore } from '@/stores/config'
import { useProjectStore } from '@/stores/project'
import { useProfileExtractor } from '@/composables/useProfileExtractor'
import ProfileExtractBar from '@/components/ProfileExtractBar.vue'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

const configStore = useConfigStore()
const projectStore = useProjectStore()

const llmConfig = ref('')
const messages = ref<ChatMessage[]>([])
const userInput = ref('')
const streaming = ref(false)
const streamContent = ref('')
const chatContainerRef = ref<HTMLElement>()

// Context toggles
const includeCoreSeed = ref(true)
const includeCharacters = ref(true)
const includeWorldBuilding = ref(true)
const includePlot = ref(true)
const includeBlueprint = ref(false)
const includeCharacterState = ref(false)
const extraContext = ref('')
const showSettings = ref(false)
const profiler = useProfileExtractor()

// Discussion mode
const discussionMode = ref('advisor')
const modeOptions = [
  { value: 'casual', label: '轻松闲聊', desc: '像朋友聊天，简短随意' },
  { value: 'advisor', label: '专业顾问', desc: '结构化建议，详细分析' },
  { value: 'brainstorm', label: '头脑风暴', desc: '多角色视角，观点碰撞' },
  { value: 'devil', label: '魔鬼代言人', desc: '挑战想法，找出弱点' },
  { value: 'roleplay', label: '角色扮演', desc: '以小说角色身份对话' },
]

const canSend = computed(() => userInput.value.trim() && llmConfig.value && !streaming.value)

function scrollToBottom() {
  nextTick(() => {
    if (chatContainerRef.value) {
      chatContainerRef.value.scrollTop = chatContainerRef.value.scrollHeight
    }
  })
}

function sendMessage() {
  const text = userInput.value.trim()
  if (!text || streaming.value) return

  // 异步提取偏好（不阻塞发送）
  profiler.tryExtract(text, llmConfig.value)

  messages.value.push({ role: 'user', content: text })
  userInput.value = ''
  streaming.value = true
  streamContent.value = ''

  scrollToBottom()

  postSSE(
    brainstormApi.chatUrl(),
    {
      llm_config_name: llmConfig.value,
      filepath: projectStore.filepath,
      messages: messages.value,
      include_core_seed: includeCoreSeed.value,
      include_characters: includeCharacters.value,
      include_world_building: includeWorldBuilding.value,
      include_plot: includePlot.value,
      include_blueprint: includeBlueprint.value,
      include_character_state: includeCharacterState.value,
      extra_context: extraContext.value,
      discussion_mode: discussionMode.value,
    },
    (_msg, _value, content) => {
      if (content) {
        streamContent.value = content
        scrollToBottom()
      }
    },
    (content) => {
      const finalContent = content || streamContent.value
      messages.value.push({ role: 'assistant', content: finalContent })
      streamContent.value = ''
    },
    (err) => {
      messages.value.push({ role: 'assistant', content: `❌ ${err}` })
      streamContent.value = ''
      streaming.value = false
    },
    () => {
      streaming.value = false
      scrollToBottom()
    },
  )
}

function clearChat() {
  messages.value = []
  streamContent.value = ''
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

onMounted(async () => {
  await Promise.all([configStore.loadAll(), projectStore.loadActive()])
  if (configStore.llmChoices.length) llmConfig.value = configStore.llmChoices[0]
})
</script>

<template>
  <div class="flex flex-col h-[calc(100vh-120px)] max-w-4xl mx-auto px-4 py-4">
    <!-- Header -->
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-3">
        <h2 class="text-2xl font-bold" style="color: var(--color-ink)">💡 创意讨论</h2>
        <div class="flex gap-1">
          <button
            v-for="m in modeOptions" :key="m.value"
            @click="discussionMode = m.value"
            :title="m.desc"
            class="px-2 py-1 rounded text-xs transition-colors"
            :class="discussionMode === m.value
              ? 'bg-[var(--color-leather)] text-[var(--color-parchment)]'
              : 'bg-[var(--color-parchment-dark)] text-[var(--color-ink-light)] hover:bg-[var(--color-parchment-darker)]'"
            type="button"
          >{{ m.label }}</button>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="showSettings = !showSettings"
          class="px-3 py-1.5 rounded-md text-sm border border-[var(--color-parchment-darker)] hover:bg-[var(--color-parchment-darker)] transition-colors"
          type="button"
        >
          {{ showSettings ? '收起设置' : '上下文设置' }}
        </button>
        <button
          @click="clearChat"
          :disabled="streaming"
          class="px-3 py-1.5 rounded-md text-sm border border-red-300 text-red-600 hover:bg-red-50 disabled:opacity-50 transition-colors"
          type="button"
        >
          清空对话
        </button>
      </div>
    </div>

    <!-- Settings Panel -->
    <Transition name="slide">
      <div
        v-if="showSettings"
        class="rounded-xl border border-[var(--color-parchment-darker)] bg-white p-4 mb-3 space-y-3"
      >
        <div class="flex gap-4 flex-wrap">
          <div class="flex-1 min-w-[200px]">
            <label class="block text-xs text-[var(--color-ink-light)] mb-1">LLM 配置</label>
            <select
              v-model="llmConfig"
              class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm"
            >
              <option v-for="c in configStore.llmChoices" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
          <div class="flex-1 min-w-[200px]">
            <label class="block text-xs text-[var(--color-ink-light)] mb-1">讨论模式</label>
            <select
              v-model="discussionMode"
              class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm"
            >
              <option v-for="m in modeOptions" :key="m.value" :value="m.value">{{ m.label }} — {{ m.desc }}</option>
            </select>
          </div>
        </div>

        <div>
          <label class="block text-xs text-[var(--color-ink-light)] mb-2">注入上下文（勾选后将包含在对话中）</label>
          <div class="flex flex-wrap gap-x-4 gap-y-2">
            <label class="inline-flex items-center gap-1.5 text-sm cursor-pointer">
              <input type="checkbox" v-model="includeCoreSeed" class="rounded" />
              核心种子
            </label>
            <label class="inline-flex items-center gap-1.5 text-sm cursor-pointer">
              <input type="checkbox" v-model="includeCharacters" class="rounded" />
              角色动力学
            </label>
            <label class="inline-flex items-center gap-1.5 text-sm cursor-pointer">
              <input type="checkbox" v-model="includeWorldBuilding" class="rounded" />
              世界观设定
            </label>
            <label class="inline-flex items-center gap-1.5 text-sm cursor-pointer">
              <input type="checkbox" v-model="includePlot" class="rounded" />
              剧情架构
            </label>
            <label class="inline-flex items-center gap-1.5 text-sm cursor-pointer">
              <input type="checkbox" v-model="includeBlueprint" class="rounded" />
              章节蓝图
            </label>
            <label class="inline-flex items-center gap-1.5 text-sm cursor-pointer">
              <input type="checkbox" v-model="includeCharacterState" class="rounded" />
              角色状态
            </label>
          </div>
        </div>

        <div>
          <label class="block text-xs text-[var(--color-ink-light)] mb-1">补充资料（可选）</label>
          <textarea
            v-model="extraContext"
            rows="2"
            class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm resize-none"
            placeholder="粘贴额外的参考资料或背景信息..."
          />
        </div>
      </div>
    </Transition>

    <!-- Chat Messages -->
    <div
      ref="chatContainerRef"
      class="flex-1 overflow-y-auto rounded-xl border border-[var(--color-parchment-darker)] bg-white p-4 space-y-4"
    >
      <!-- Empty state -->
      <div
        v-if="messages.length === 0 && !streaming"
        class="flex flex-col items-center justify-center h-full text-[var(--color-ink-light)] opacity-60"
      >
        <span class="text-4xl mb-3">💡</span>
        <p class="text-sm">在下方输入你的创作想法、疑问或需要讨论的方向</p>
        <p class="text-xs mt-1">当前模式：<strong>{{ modeOptions.find(m => m.value === discussionMode)?.label }}</strong> — {{ modeOptions.find(m => m.value === discussionMode)?.desc }}</p>
      </div>

      <!-- Messages -->
      <div
        v-for="(msg, i) in messages"
        :key="i"
        class="flex"
        :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
      >
        <div
          class="max-w-[80%] rounded-xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap"
          :class="
            msg.role === 'user'
              ? 'bg-[var(--color-leather)] text-[var(--color-parchment)]'
              : 'bg-[var(--color-parchment-dark)] text-[var(--color-ink)]'
          "
        >{{ msg.content }}</div>
      </div>

      <!-- Streaming message -->
      <div v-if="streaming && streamContent" class="flex justify-start">
        <div
          class="max-w-[80%] rounded-xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap bg-[var(--color-parchment-dark)] text-[var(--color-ink)]"
        >
          {{ streamContent }}
          <span class="inline-block w-2 h-4 ml-0.5 bg-[var(--color-ink)] animate-pulse" />
        </div>
      </div>

      <!-- Loading indicator -->
      <div v-if="streaming && !streamContent" class="flex justify-start">
        <div class="rounded-xl px-4 py-3 bg-[var(--color-parchment-dark)] text-[var(--color-ink-light)] text-sm italic">
          思考中...
          <span class="inline-block w-2 h-4 ml-0.5 bg-[var(--color-ink-light)] animate-pulse" />
        </div>
      </div>
    </div>

    <!-- 偏好提取确认 -->
    <ProfileExtractBar
      :show="profiler.showConfirm.value"
      :preferences="profiler.extractedPrefs.value"
      :confirm-msg="profiler.confirmMsg.value"
      @confirm="profiler.confirmAppend()"
      @dismiss="profiler.dismissExtract()"
    />

    <!-- Input Area -->
    <div class="mt-3 flex gap-2">
      <textarea
        v-model="userInput"
        @keydown="handleKeydown"
        :disabled="streaming"
        rows="2"
        class="flex-1 border border-[var(--color-parchment-darker)] rounded-xl px-4 py-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-[var(--color-leather)] disabled:opacity-50"
        placeholder="输入你的想法、疑问或方向... (Enter 发送, Shift+Enter 换行)"
      />
      <button
        @click="sendMessage"
        :disabled="!canSend"
        class="px-5 self-end rounded-xl text-sm font-semibold h-[46px] disabled:opacity-50 transition-colors"
        style="background-color: var(--color-leather); color: var(--color-parchment)"
        type="button"
      >
        {{ streaming ? '回复中...' : '发送' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: all 0.2s ease;
}
.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  max-height: 0;
  overflow: hidden;
}
.slide-enter-to,
.slide-leave-from {
  opacity: 1;
  max-height: 500px;
}
</style>
