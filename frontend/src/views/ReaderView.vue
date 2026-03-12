<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useLocalStorage } from '@vueuse/core'
import { generateApi } from '@/api/client'
import { useProjectStore } from '@/stores/project'

interface ChapterInfo {
  num: number
  has_draft: boolean
  has_final: boolean
}

const projectStore = useProjectStore()

const chapters = ref<ChapterInfo[]>([])
const currentChapter = ref<number | null>(null)
const currentContent = ref('')
const allContents = ref<{ num: number; content: string }[]>([])
const mode = ref<'single' | 'all'>('single')
const loading = ref(false)
const loadingList = ref(false)

const fontSize = useLocalStorage('reader-font-size', 16)

const currentIndex = computed(() =>
  chapters.value.findIndex((c) => c.num === currentChapter.value),
)
const hasPrev = computed(() => currentIndex.value > 0)
const hasNext = computed(() => currentIndex.value < chapters.value.length - 1)

async function loadChapterList() {
  loadingList.value = true
  try {
    const res = await generateApi.chapters(projectStore.filepath)
    chapters.value = res.data.chapters ?? []
  } catch {
    chapters.value = []
  } finally {
    loadingList.value = false
  }
}

async function loadChapter(num: number) {
  currentChapter.value = num
  loading.value = true
  try {
    const res = await generateApi.getChapter(num, projectStore.filepath)
    currentContent.value = res.data.content ?? ''
  } catch (e: unknown) {
    currentContent.value = `加载失败: ${(e as Error).message}`
  } finally {
    loading.value = false
  }
}

async function loadAllChapters() {
  loading.value = true
  allContents.value = []
  try {
    const withContent = chapters.value.filter((c) => c.has_final || c.has_draft)
    const results = await Promise.all(
      withContent.map(async (c) => {
        const res = await generateApi.getChapter(c.num, projectStore.filepath)
        return { num: c.num, content: res.data.content ?? '' }
      }),
    )
    allContents.value = results.sort((a, b) => a.num - b.num)
  } catch {
    /* ignore */
  } finally {
    loading.value = false
  }
}

function prevChapter() {
  if (!hasPrev.value) return
  loadChapter(chapters.value[currentIndex.value - 1].num)
}

function nextChapter() {
  if (!hasNext.value) return
  loadChapter(chapters.value[currentIndex.value + 1].num)
}

function adjustFontSize(delta: number) {
  const next = fontSize.value + delta
  if (next >= 12 && next <= 28) fontSize.value = next
}

function switchMode(m: 'single' | 'all') {
  mode.value = m
  if (m === 'all') loadAllChapters()
}

onMounted(async () => {
  await projectStore.loadActive()
  await loadChapterList()
})

watch(() => projectStore.filepath, loadChapterList)
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-6 space-y-4">
    <h2 class="text-2xl font-bold" style="color: var(--color-ink)">📖 小说阅读</h2>

    <div class="grid grid-cols-1 lg:grid-cols-4 gap-4">
      <!-- 左侧：章节列表 -->
      <div
        class="lg:col-span-1 rounded-xl border border-[var(--color-parchment-darker)] bg-white overflow-hidden"
      >
        <div
          class="px-4 py-3 bg-[var(--color-parchment)] border-b border-[var(--color-parchment-darker)] flex items-center justify-between"
        >
          <span class="font-medium text-sm text-[var(--color-leather)]">章节列表</span>
          <button
            @click="loadChapterList"
            class="text-xs text-[var(--color-ink-light)] hover:text-[var(--color-leather)] transition-colors"
            type="button"
          >
            🔄
          </button>
        </div>
        <div class="overflow-y-auto" style="max-height: 70vh">
          <div v-if="loadingList" class="p-4 text-sm text-[var(--color-ink-light)] italic">
            加载中…
          </div>
          <div
            v-else-if="chapters.length === 0"
            class="p-4 text-sm text-[var(--color-ink-light)] italic"
          >
            暂无章节，请先在创作工坊中生成章节。
          </div>
          <div v-else>
            <button
              v-for="ch in chapters"
              :key="ch.num"
              @click="loadChapter(ch.num)"
              class="w-full text-left px-4 py-2.5 text-sm hover:bg-[var(--color-parchment)] transition-colors flex items-center justify-between gap-2 border-b border-[var(--color-parchment-dark)]"
              :class="
                currentChapter === ch.num
                  ? 'bg-[var(--color-parchment)] font-medium text-[var(--color-leather)]'
                  : 'text-[var(--color-ink)]'
              "
              type="button"
            >
              <span>第 {{ ch.num }} 章</span>
              <span
                class="text-xs px-1.5 py-0.5 rounded"
                :class="
                  ch.has_final
                    ? 'bg-[var(--color-success)] text-white'
                    : ch.has_draft
                      ? 'bg-[var(--color-warning)] text-white'
                      : 'bg-[var(--color-parchment-dark)] text-[var(--color-ink-light)]'
                "
              >
                {{ ch.has_final ? '定稿' : ch.has_draft ? '草稿' : '空' }}
              </span>
            </button>
          </div>
        </div>
      </div>

      <!-- 右侧：阅读区 -->
      <div
        class="lg:col-span-3 rounded-xl border border-[var(--color-parchment-darker)] bg-white overflow-hidden flex flex-col"
      >
        <!-- 工具栏 -->
        <div
          class="px-4 py-3 bg-[var(--color-parchment)] border-b border-[var(--color-parchment-darker)] flex items-center justify-between flex-wrap gap-2"
        >
          <span class="font-medium text-sm text-[var(--color-leather)]">
            {{
              mode === 'single' && currentChapter
                ? `第 ${currentChapter} 章`
                : mode === 'all'
                  ? '全部章节'
                  : '请选择章节'
            }}
          </span>
          <div class="flex items-center gap-3">
            <!-- 字号调节 -->
            <div class="flex items-center gap-1">
              <button
                @click="adjustFontSize(-1)"
                class="border border-[var(--color-parchment-darker)] rounded px-2 py-0.5 text-xs hover:bg-white transition-colors"
                type="button"
                title="缩小字号"
              >
                A-
              </button>
              <span class="text-xs text-[var(--color-ink-light)] w-8 text-center">{{
                fontSize
              }}</span>
              <button
                @click="adjustFontSize(1)"
                class="border border-[var(--color-parchment-darker)] rounded px-2 py-0.5 text-xs hover:bg-white transition-colors"
                type="button"
                title="放大字号"
              >
                A+
              </button>
            </div>
            <!-- 模式切换 -->
            <div
              class="flex rounded-md border border-[var(--color-parchment-darker)] overflow-hidden"
            >
              <button
                @click="switchMode('single')"
                class="px-3 py-1 text-xs transition-colors"
                :class="
                  mode === 'single'
                    ? 'bg-[var(--color-leather)] text-white'
                    : 'hover:bg-[var(--color-parchment-dark)]'
                "
                type="button"
              >
                单章
              </button>
              <button
                @click="switchMode('all')"
                class="px-3 py-1 text-xs transition-colors"
                :class="
                  mode === 'all'
                    ? 'bg-[var(--color-leather)] text-white'
                    : 'hover:bg-[var(--color-parchment-dark)]'
                "
                type="button"
              >
                全部
              </button>
            </div>
          </div>
        </div>

        <!-- 内容区 -->
        <div class="flex-1 overflow-y-auto p-6" style="max-height: 70vh">
          <div v-if="loading" class="text-sm text-[var(--color-ink-light)] italic text-center py-8">
            加载中…
          </div>

          <!-- 单章模式 -->
          <template v-else-if="mode === 'single'">
            <div v-if="!currentChapter" class="text-sm text-[var(--color-ink-light)] italic text-center py-8">
              点击左侧章节开始阅读
            </div>
            <div
              v-else
              class="mx-auto leading-relaxed whitespace-pre-wrap"
              :style="{
                fontSize: fontSize + 'px',
                color: 'var(--color-ink)',
                maxWidth: '680px',
                fontFamily: 'var(--font-serif)',
                lineHeight: '1.8',
              }"
            >
              {{ currentContent }}
            </div>
          </template>

          <!-- 全部模式 -->
          <template v-else>
            <div
              v-if="allContents.length === 0 && !loading"
              class="text-sm text-[var(--color-ink-light)] italic text-center py-8"
            >
              暂无已有内容的章节
            </div>
            <div v-else class="mx-auto space-y-8" style="max-width: 680px">
              <div v-for="item in allContents" :key="item.num">
                <h3
                  class="text-lg font-bold mb-4 pb-2 border-b border-[var(--color-parchment-darker)]"
                  style="color: var(--color-leather)"
                >
                  第 {{ item.num }} 章
                </h3>
                <div
                  class="leading-relaxed whitespace-pre-wrap"
                  :style="{
                    fontSize: fontSize + 'px',
                    color: 'var(--color-ink)',
                    fontFamily: 'var(--font-serif)',
                    lineHeight: '1.8',
                  }"
                >
                  {{ item.content }}
                </div>
              </div>
            </div>
          </template>
        </div>

        <!-- 底部导航（仅单章模式） -->
        <div
          v-if="mode === 'single' && currentChapter"
          class="px-4 py-3 bg-[var(--color-parchment)] border-t border-[var(--color-parchment-darker)] flex items-center justify-between"
        >
          <button
            @click="prevChapter"
            :disabled="!hasPrev"
            class="border border-[var(--color-parchment-darker)] rounded-md px-4 py-1.5 text-sm transition-colors"
            :class="
              hasPrev
                ? 'hover:bg-white text-[var(--color-ink)]'
                : 'opacity-40 cursor-not-allowed text-[var(--color-ink-light)]'
            "
            type="button"
          >
            ← 上一章
          </button>
          <span class="text-xs text-[var(--color-ink-light)]">
            {{ currentIndex + 1 }} / {{ chapters.length }}
          </span>
          <button
            @click="nextChapter"
            :disabled="!hasNext"
            class="border border-[var(--color-parchment-darker)] rounded-md px-4 py-1.5 text-sm transition-colors"
            :class="
              hasNext
                ? 'hover:bg-white text-[var(--color-ink)]'
                : 'opacity-40 cursor-not-allowed text-[var(--color-ink-light)]'
            "
            type="button"
          >
            下一章 →
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
