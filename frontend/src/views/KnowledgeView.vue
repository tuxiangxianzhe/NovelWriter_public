<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { knowledgeApi } from '@/api/client'
import { useConfigStore } from '@/stores/config'
import { useProjectStore } from '@/stores/project'

const configStore = useConfigStore()
const projectStore = useProjectStore()
const embConfig = ref('')
const statusMsg = ref('')

// 知识库
const knowledgeFile = ref<File | null>(null)
const importingKnowledge = ref(false)

function onKnowledgeFile(e: Event) {
  knowledgeFile.value = (e.target as HTMLInputElement).files?.[0] ?? null
}

async function importKnowledge() {
  if (!knowledgeFile.value) return
  importingKnowledge.value = true
  try {
    const fd = new FormData()
    fd.append('emb_config_name', embConfig.value)
    fd.append('filepath', projectStore.filepath)
    fd.append('file', knowledgeFile.value)
    await knowledgeApi.import(fd)
    statusMsg.value = '✅ 知识库导入成功!'
  } catch (e: unknown) {
    statusMsg.value = `❌ ${(e as Error).message}`
  } finally {
    importingKnowledge.value = false
  }
}

async function clearKnowledge() {
  if (!confirm('确认清空知识库？')) return
  try {
    const res = await knowledgeApi.clear(projectStore.filepath)
    statusMsg.value = res.data.message
  } catch (e: unknown) {
    statusMsg.value = `❌ ${(e as Error).message}`
  }
}

onMounted(async () => {
  await Promise.all([configStore.loadAll(), projectStore.loadActive()])
  if (configStore.embeddingChoices.length) embConfig.value = configStore.embeddingChoices[0]
})
</script>

<template>
  <div class="max-w-3xl mx-auto px-4 py-6 space-y-6">
    <h2 class="text-2xl font-bold" style="color: var(--color-ink)">📚 知识库</h2>

    <Transition name="fade">
      <div v-if="statusMsg" class="px-4 py-2 rounded-md text-sm"
        :class="statusMsg.startsWith('✅') ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'">
        {{ statusMsg }}
      </div>
    </Transition>

    <div>
      <label class="block text-xs text-[var(--color-ink-light)] mb-1">Embedding 配置</label>
      <select v-model="embConfig" class="border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm w-full max-w-xs">
        <option v-for="c in configStore.embeddingChoices" :key="c" :value="c">{{ c }}</option>
      </select>
    </div>

    <!-- 知识库 -->
    <div class="rounded-xl border border-[var(--color-parchment-darker)] bg-white p-5 space-y-3">
      <h3 class="font-semibold text-[var(--color-leather)]">知识库（RAG 检索）</h3>
      <p class="text-sm text-[var(--color-ink-light)]">上传 .txt 文件作为知识库，章节生成时自动检索相关内容。</p>
      <input type="file" accept=".txt" @change="onKnowledgeFile" class="text-sm text-[var(--color-ink)] file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-sm file:font-medium file:cursor-pointer" style="file:background-color: var(--color-leather); file:color: var(--color-parchment)" />
      <div class="flex gap-2">
        <button @click="importKnowledge" :disabled="importingKnowledge || !knowledgeFile || !embConfig"
          class="px-4 py-2 rounded-md text-sm font-semibold disabled:opacity-50" style="background-color: var(--color-leather); color: var(--color-parchment)" type="button">
          {{ importingKnowledge ? '导入中…' : '▶ 导入知识库' }}
        </button>
        <button @click="clearKnowledge"
          class="px-4 py-2 rounded-md text-sm border border-red-200 text-red-600 hover:bg-red-50 transition-colors" type="button">
          清空知识库
        </button>
      </div>
    </div>

    <p class="text-xs text-[var(--color-ink-light)] italic">作者参考库已移至「文风与叙事DNA」页面，绑定到具体文风。</p>
  </div>
</template>
