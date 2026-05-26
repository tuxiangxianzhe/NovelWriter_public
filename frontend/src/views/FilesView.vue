<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { filesApi } from '@/api/client'
import { useProjectStore } from '@/stores/project'

interface FileEntry {
  path: string
  name: string
  size: number
  directory: string
}

const projectStore = useProjectStore()
const files = ref<FileEntry[]>([])
const selectedFile = ref<FileEntry | null>(null)
const fileContent = ref('')
const editContent = ref('')
const editing = ref(false)
const loading = ref(false)
const loadingContent = ref(false)
const saving = ref(false)
const saveMsg = ref('')

const isDirty = computed(() => editing.value && editContent.value !== fileContent.value)

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}

async function loadFiles() {
  loading.value = true
  try {
    const res = await filesApi.list(projectStore.filepath)
    files.value = res.data.files
  } catch { /* ignore */ } finally {
    loading.value = false }
}

async function loadContent(f: FileEntry) {
  if (isDirty.value && !confirm('当前文件有未保存的修改，是否放弃？')) return
  editing.value = false
  selectedFile.value = f
  loadingContent.value = true
  saveMsg.value = ''
  try {
    const res = await filesApi.content(projectStore.filepath, f.path)
    fileContent.value = res.data.content
    editContent.value = fileContent.value
  } catch (e: unknown) {
    fileContent.value = `❌ 读取失败: ${(e as Error).message}`
    editContent.value = fileContent.value
  } finally {
    loadingContent.value = false
  }
}

function enterEdit() {
  editContent.value = fileContent.value
  editing.value = true
  saveMsg.value = ''
}

function cancelEdit() {
  editing.value = false
  editContent.value = fileContent.value
  saveMsg.value = ''
}

async function saveFile() {
  if (!selectedFile.value) return
  saving.value = true
  saveMsg.value = ''
  try {
    await filesApi.save(projectStore.filepath, selectedFile.value.path, editContent.value)
    fileContent.value = editContent.value
    editing.value = false
    saveMsg.value = '✅ 已保存'
    // Refresh file list to update sizes
    loadFiles()
    setTimeout(() => (saveMsg.value = ''), 3000)
  } catch (e: unknown) {
    saveMsg.value = `❌ 保存失败: ${(e as Error).message}`
  } finally {
    saving.value = false
  }
}

// 按目录分组
const grouped = ref<Record<string, FileEntry[]>>({})
watch(files, (flist) => {
  const g: Record<string, FileEntry[]> = {}
  for (const f of flist) {
    const dir = f.directory || '.'
    if (!g[dir]) g[dir] = []
    g[dir].push(f)
  }
  grouped.value = g
})

onMounted(async () => {
  await projectStore.loadActive()
  await loadFiles()
})

watch(() => projectStore.filepath, loadFiles)
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 py-6 space-y-4">
    <div class="flex items-center justify-between flex-wrap gap-2">
      <h2 class="text-2xl font-bold" style="color: var(--color-ink)">📁 文件管理</h2>
      <button @click="loadFiles" class="border border-[var(--color-parchment-darker)] rounded-md px-3 py-1.5 text-sm hover:bg-[var(--color-parchment)] transition-colors" type="button">
        🔄 刷新
      </button>
    </div>

    <p class="text-sm text-[var(--color-ink-light)]">路径：<code class="font-mono bg-[var(--color-parchment-dark)] px-1 rounded">{{ projectStore.filepath }}</code></p>

    <div class="grid grid-cols-1 lg:grid-cols-5 gap-4">
      <!-- 文件树 -->
      <div class="lg:col-span-2 rounded-xl border border-[var(--color-parchment-darker)] bg-white overflow-hidden">
        <div class="px-4 py-3 bg-[var(--color-parchment)] border-b border-[var(--color-parchment-darker)]">
          <span class="font-medium text-sm text-[var(--color-leather)]">文件列表</span>
        </div>
        <div class="overflow-y-auto" style="max-height: 600px">
          <div v-if="loading" class="p-4 text-sm text-[var(--color-ink-light)] italic">加载中…</div>
          <div v-else-if="files.length === 0" class="p-4 text-sm text-[var(--color-ink-light)] italic">暂无文件</div>
          <div v-else>
            <div v-for="(group, dir) in grouped" :key="dir">
              <div class="px-3 py-1.5 bg-[var(--color-parchment-dark)] text-xs font-medium text-[var(--color-ink-light)] sticky top-0">
                {{ dir }}
              </div>
              <button
                v-for="f in group"
                :key="f.path"
                @click="loadContent(f)"
                class="w-full text-left px-4 py-2 text-sm hover:bg-[var(--color-parchment)] transition-colors flex items-center justify-between gap-2"
                :class="selectedFile?.path === f.path ? 'bg-[var(--color-parchment)] font-medium' : ''"
                type="button"
              >
                <span class="truncate">{{ f.name }}</span>
                <span class="text-xs text-[var(--color-ink-light)] whitespace-nowrap">{{ formatSize(f.size) }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 文件内容 -->
      <div class="lg:col-span-3 rounded-xl border border-[var(--color-parchment-darker)] bg-white overflow-hidden flex flex-col">
        <div class="px-4 py-3 bg-[var(--color-parchment)] border-b border-[var(--color-parchment-darker)] flex items-center justify-between flex-wrap gap-2">
          <div class="flex items-center gap-2">
            <span class="font-medium text-sm text-[var(--color-leather)]">
              {{ selectedFile ? selectedFile.path : '请选择文件' }}
            </span>
            <span v-if="saveMsg" class="text-xs" :class="saveMsg.startsWith('✅') ? 'text-green-600' : 'text-red-500'">
              {{ saveMsg }}
            </span>
            <span v-if="isDirty" class="text-xs text-amber-500 font-medium">● 未保存</span>
          </div>
          <div v-if="selectedFile && fileContent && !loadingContent" class="flex items-center gap-2">
            <template v-if="!editing">
              <button
                @click="enterEdit"
                class="border border-[var(--color-parchment-darker)] rounded px-3 py-1 text-xs hover:bg-white transition-colors text-[var(--color-ink)]"
                type="button"
              >
                ✏️ 编辑
              </button>
            </template>
            <template v-else>
              <button
                @click="saveFile"
                :disabled="saving || !isDirty"
                class="rounded px-3 py-1 text-xs transition-colors text-white"
                :class="saving || !isDirty ? 'bg-gray-300 cursor-not-allowed' : 'bg-[var(--color-success)] hover:opacity-90'"
                type="button"
              >
                {{ saving ? '保存中…' : '💾 保存' }}
              </button>
              <button
                @click="cancelEdit"
                :disabled="saving"
                class="border border-[var(--color-parchment-darker)] rounded px-3 py-1 text-xs hover:bg-white transition-colors text-[var(--color-ink)]"
                type="button"
              >
                取消
              </button>
            </template>
          </div>
        </div>
        <div class="flex-1 p-4 overflow-y-auto" style="max-height: 600px">
          <div v-if="loadingContent" class="text-sm text-[var(--color-ink-light)] italic">加载中…</div>
          <textarea
            v-else-if="editing"
            v-model="editContent"
            class="w-full h-full text-sm font-mono whitespace-pre-wrap leading-relaxed text-[var(--color-ink)] resize-none outline-none border border-[var(--color-parchment-darker)] rounded-lg p-3"
            style="min-height: 550px"
          />
          <pre v-else-if="fileContent" class="text-sm font-mono whitespace-pre-wrap leading-relaxed text-[var(--color-ink)]">{{ fileContent }}</pre>
          <p v-else class="text-sm text-[var(--color-ink-light)] italic">点击左侧文件查看内容</p>
        </div>
      </div>
    </div>
  </div>
</template>
