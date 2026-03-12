<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { stylesApi, postSSE } from '@/api/client'
import { useConfigStore } from '@/stores/config'
import StreamOutput from '@/components/StreamOutput.vue'

const configStore = useConfigStore()
const styleList = ref<string[]>([])
const selectedStyle = ref('')
const styleInstruction = ref('')
const analysisResult = ref('')
const sourceSample = ref('')
const calibrationReference = ref('')
const hasCalibrationSnapshot = ref(false)
const snapshotTimestamp = ref('')
const narrativeForArch = ref('')
const narrativeForBp = ref('')
const narrativeForCh = ref('')
const statusMsg = ref('')

// 分析
const analyzeLLM = ref('')
const sampleText = ref('')
const newStyleName = ref('')
const analyzeState = ref({ running: false, progress: '', result: '', error: '' })

// DNA 分析
const dnaSampleText = ref('')
const dnaState = ref({ running: false, progress: '', result: '', error: '' })

// 迭代校准（文风）
const calibrateMaxIter = ref(5)
const calibrateState = ref({ running: false, progress: '', result: '', error: '' })

// 迭代校准（叙事DNA章节指令）
const narrativeCalibrateMaxIter = ref(5)
const narrativeCalibrateState = ref({ running: false, progress: '', result: '', error: '' })

// 融合
const mergeSelected = ref<string[]>([])
const mergeName = ref('')
const mergePreference = ref('')
const mergeState = ref({ running: false, progress: '', result: '', error: '' })

// 解锁模式（绕过内容审查）
const unlock = ref(false)

// 作者参考库
const authorRefFiles = ref<File[]>([])
const authorRefImporting = ref(false)
const authorRefExists = ref(false)
const authorRefEmbConfig = ref('')
const authorRefMsg = ref('')

function onAuthorRefFile(e: Event) {
  const files = (e.target as HTMLInputElement).files
  authorRefFiles.value = files ? Array.from(files) : []
}

async function loadAuthorRefStatus(name: string) {
  if (!name) { authorRefExists.value = false; return }
  try {
    const res = await stylesApi.authorRefStatus(name)
    authorRefExists.value = res.data.has_author_reference
  } catch { authorRefExists.value = false }
}

async function importAuthorRef() {
  if (!selectedStyle.value || !authorRefFiles.value.length || !authorRefEmbConfig.value) return
  authorRefImporting.value = true
  authorRefMsg.value = ''
  const total = authorRefFiles.value.length
  let success = 0
  let failed = 0
  for (let i = 0; i < total; i++) {
    const file = authorRefFiles.value[i]
    authorRefMsg.value = `导入中… (${i + 1}/${total}) ${file.name}`
    try {
      const fd = new FormData()
      fd.append('emb_config_name', authorRefEmbConfig.value)
      fd.append('file', file)
      await stylesApi.importAuthorRef(selectedStyle.value, fd)
      success++
    } catch {
      failed++
    }
  }
  authorRefExists.value = success > 0
  authorRefMsg.value = failed
    ? `✅ 导入完成：${success} 个成功，${failed} 个失败`
    : `✅ ${success} 个文件全部导入成功!`
  authorRefImporting.value = false
}

async function clearAuthorRef() {
  if (!selectedStyle.value) return
  if (!confirm(`确认清空文风「${selectedStyle.value}」的作者参考库？`)) return
  try {
    const res = await stylesApi.clearAuthorRef(selectedStyle.value)
    authorRefMsg.value = res.data.message
    authorRefExists.value = false
  } catch (e: unknown) {
    authorRefMsg.value = `❌ ${(e as Error).message}`
  }
}

async function loadStyles() {
  const res = await stylesApi.list()
  styleList.value = res.data.styles
}

async function loadStyle(name: string) {
  if (!name) return
  try {
    const res = await stylesApi.get(name)
    styleInstruction.value = res.data.style_instruction
    analysisResult.value = res.data.analysis_result
    sourceSample.value = res.data.source_sample ?? ''
    calibrationReference.value = res.data.calibration_reference ?? ''
    hasCalibrationSnapshot.value = res.data.has_calibration_snapshot ?? false
    snapshotTimestamp.value = res.data.snapshot_timestamp ?? ''
    narrativeForArch.value = res.data.narrative_for_architecture ?? ''
    narrativeForBp.value = res.data.narrative_for_blueprint ?? ''
    narrativeForCh.value = res.data.narrative_for_chapter ?? ''
    loadAuthorRefStatus(name)
  } catch (e: unknown) {
    statusMsg.value = `❌ ${(e as Error).message}`
  }
}

async function saveStyle() {
  if (!selectedStyle.value) return
  try {
    await stylesApi.save(selectedStyle.value, {
      analysis_result: analysisResult.value,
      style_instruction: styleInstruction.value,
      source_sample: sourceSample.value,
      calibration_reference: calibrationReference.value,
      narrative_for_architecture: narrativeForArch.value,
      narrative_for_blueprint: narrativeForBp.value,
      narrative_for_chapter: narrativeForCh.value,
    })
    statusMsg.value = `✅ 文风「${selectedStyle.value}」已保存`
  } catch (e: unknown) {
    statusMsg.value = `❌ ${(e as Error).message}`
  }
}

async function deleteStyle() {
  if (!selectedStyle.value) return
  if (!confirm(`确认删除文风「${selectedStyle.value}」？`)) return
  try {
    await stylesApi.delete(selectedStyle.value)
    await loadStyles()
    selectedStyle.value = ''
    styleInstruction.value = ''
    analysisResult.value = ''
    sourceSample.value = ''
    calibrationReference.value = ''
    hasCalibrationSnapshot.value = false
    snapshotTimestamp.value = ''
    narrativeForArch.value = ''
    narrativeForBp.value = ''
    narrativeForCh.value = ''
    statusMsg.value = '✅ 已删除'
  } catch (e: unknown) {
    statusMsg.value = `❌ ${(e as Error).message}`
  }
}

function runSSE(
  state: typeof analyzeState.value,
  url: string,
  body: Record<string, unknown>,
) {
  state.running = true; state.progress = ''; state.result = ''; state.error = ''
  postSSE(url, body,
    (msg) => { state.progress = msg },
    (content) => { state.result = content; loadStyles() },
    (err) => { state.error = err; state.running = false },
    () => { state.running = false },
  )
}

function doAnalyze() {
  if (!analyzeLLM.value || !newStyleName.value || !sampleText.value) return
  runSSE(analyzeState.value, '/styles/analyze', {
    llm_config_name: analyzeLLM.value,
    sample_text: sampleText.value,
    style_name: newStyleName.value,
    unlock: unlock.value,
  })
}

function doAnalyzeDNA() {
  if (!analyzeLLM.value || !selectedStyle.value || !dnaSampleText.value) return
  runSSE(dnaState.value, '/styles/analyze-dna', {
    llm_config_name: analyzeLLM.value,
    sample_text: dnaSampleText.value,
    style_name: selectedStyle.value,
    unlock: unlock.value,
  })
}

function doCalibrate() {
  if (!analyzeLLM.value || !selectedStyle.value) return
  const st = calibrateState.value
  st.running = true; st.progress = ''; st.result = ''; st.error = ''
  postSSE('/styles/calibrate', {
    llm_config_name: analyzeLLM.value,
    style_name: selectedStyle.value,
    max_iterations: calibrateMaxIter.value,
    unlock: unlock.value,
  },
    (msg) => { st.progress = msg },
    (content) => { st.result = content; loadStyle(selectedStyle.value) },
    (err) => { st.error = err; st.running = false },
    () => { st.running = false },
  )
}

function doCalibrateNarrative() {
  if (!analyzeLLM.value || !selectedStyle.value) return
  const st = narrativeCalibrateState.value
  st.running = true; st.progress = ''; st.result = ''; st.error = ''
  postSSE('/styles/calibrate-narrative', {
    llm_config_name: analyzeLLM.value,
    style_name: selectedStyle.value,
    max_iterations: narrativeCalibrateMaxIter.value,
    unlock: unlock.value,
  },
    (msg) => { st.progress = msg },
    (content) => { st.result = content; loadStyle(selectedStyle.value) },
    (err) => { st.error = err; st.running = false },
    () => { st.running = false },
  )
}

async function doRollback() {
  if (!selectedStyle.value) return
  if (!confirm(`确认回滚文风「${selectedStyle.value}」到校准前状态？`)) return
  try {
    await stylesApi.rollbackCalibration(selectedStyle.value)
    await loadStyle(selectedStyle.value)
    statusMsg.value = `✅ 文风「${selectedStyle.value}」已回滚到校准前状态`
  } catch (e: unknown) {
    statusMsg.value = `❌ ${(e as Error).message}`
  }
}

function doMerge() {
  if (!analyzeLLM.value || mergeSelected.value.length < 2 || !mergeName.value) return
  runSSE(mergeState.value, '/styles/merge', {
    llm_config_name: analyzeLLM.value,
    selected_styles: mergeSelected.value,
    merge_name: mergeName.value,
    user_preference: mergePreference.value,
    unlock: unlock.value,
  })
}

onMounted(async () => {
  await configStore.loadAll()
  await loadStyles()
  if (configStore.llmChoices.length) {
    analyzeLLM.value = configStore.llmChoices[0]
  }
  if (configStore.embeddingChoices.length) {
    authorRefEmbConfig.value = configStore.embeddingChoices[0]
  }
})
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-6 space-y-6">
    <h2 class="text-2xl font-bold" style="color: var(--color-ink)">🎨 文风与叙事DNA</h2>

    <Transition name="fade">
      <div v-if="statusMsg" class="px-4 py-2 rounded-md text-sm"
        :class="statusMsg.startsWith('✅') ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'">
        {{ statusMsg }}
      </div>
    </Transition>

    <!-- 全局 LLM 配置 -->
    <div class="flex items-center gap-3">
      <label class="text-xs text-[var(--color-ink-light)] whitespace-nowrap">LLM 配置</label>
      <select v-model="analyzeLLM" class="border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm flex-1 max-w-xs">
        <option v-for="c in configStore.llmChoices" :key="c" :value="c">{{ c }}</option>
      </select>
      <label class="flex items-center gap-1.5 text-xs text-[var(--color-ink-light)] whitespace-nowrap cursor-pointer select-none">
        <input type="checkbox" v-model="unlock" class="accent-amber-600" />
        内容解锁
      </label>
    </div>

    <!-- 文风列表 + 编辑 -->
    <div class="rounded-xl border border-[var(--color-parchment-darker)] bg-white p-5 space-y-4">
      <h3 class="font-semibold text-[var(--color-leather)]">文风库</h3>
      <div class="flex gap-2 flex-wrap">
        <select v-model="selectedStyle" @change="loadStyle(selectedStyle)"
          class="border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm flex-1">
          <option value="">— 选择文风 —</option>
          <option v-for="s in styleList" :key="s" :value="s">{{ s }}</option>
        </select>
        <button @click="deleteStyle" :disabled="!selectedStyle"
          class="border border-red-200 text-red-600 rounded-md px-3 py-2 text-sm hover:bg-red-50 disabled:opacity-40 transition-colors" type="button">
          删除
        </button>
      </div>
      <div v-if="selectedStyle" class="space-y-3">
        <div>
          <label class="block text-xs text-[var(--color-ink-light)] mb-1">风格指令摘要（注入章节提示词）</label>
          <textarea v-model="styleInstruction" rows="4" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm font-mono resize-y" />
        </div>
        <div>
          <label class="block text-xs text-[var(--color-ink-light)] mb-1">分析报告（完整）</label>
          <textarea v-model="analysisResult" rows="8" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm font-mono resize-y" />
        </div>
        <details class="border border-[var(--color-parchment-darker)] rounded-lg">
          <summary class="px-4 py-2 cursor-pointer text-sm font-medium text-[var(--color-leather)] select-none">
            原始样本文本（校准对比用）
          </summary>
          <div class="px-4 pb-4 pt-2 space-y-3">
            <div>
              <p class="text-xs text-[var(--color-ink-light)] mb-2">原始样本：作为参考文本A，迭代校准时LLM可看到其作者身份。文风校准取前5000字，叙事校准取前3000字。</p>
              <textarea v-model="sourceSample" rows="8" placeholder="原始样本文本…" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm font-mono resize-y" />
            </div>
            <div>
              <p class="text-xs text-[var(--color-ink-light)] mb-2">校准参考样本（第二段，同一作者的不同段落）：图灵盲测时作为"真"文本与AI生成文本混在一起，让判别器猜哪段是仿写。</p>
              <textarea v-model="calibrationReference" rows="8" placeholder="校准参考样本（同一作者的另一段文本）…" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm font-mono resize-y" />
            </div>
          </div>
        </details>
        <details class="border border-[var(--color-parchment-darker)] rounded-lg">
          <summary class="px-4 py-2 cursor-pointer text-sm font-medium text-[var(--color-leather)] select-none">
            叙事DNA编辑（架构/蓝图/章节分层指令）
          </summary>
          <div class="px-4 pb-4 pt-2 space-y-3">
            <div>
              <label class="block text-xs text-[var(--color-ink-light)] mb-1">叙事DNA - 架构层</label>
              <textarea v-model="narrativeForArch" rows="4" placeholder="架构层叙事指令…" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm font-mono resize-y" />
            </div>
            <div>
              <label class="block text-xs text-[var(--color-ink-light)] mb-1">叙事DNA - 蓝图层</label>
              <textarea v-model="narrativeForBp" rows="4" placeholder="蓝图层叙事指令…" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm font-mono resize-y" />
            </div>
            <div>
              <label class="block text-xs text-[var(--color-ink-light)] mb-1">叙事DNA - 章节层</label>
              <textarea v-model="narrativeForCh" rows="4" placeholder="章节层叙事指令…" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm font-mono resize-y" />
            </div>
          </div>
        </details>
        <!-- 作者参考库 -->
        <details class="border border-[var(--color-parchment-darker)] rounded-lg">
          <summary class="px-4 py-2 cursor-pointer text-sm font-medium text-[var(--color-leather)] select-none">
            作者参考库
            <span v-if="authorRefExists" class="ml-2 text-xs text-green-600 font-normal">已导入</span>
            <span v-else class="ml-2 text-xs text-[var(--color-ink-light)] font-normal">未导入</span>
          </summary>
          <div class="px-4 pb-4 pt-2 space-y-3">
            <p class="text-xs text-[var(--color-ink-light)]">上传目标作者的原文作品(.txt)，生成章节时自动检索相关片段辅助文风仿写。绑定到当前文风，所有使用此文风的项目共享。</p>
            <Transition name="fade">
              <div v-if="authorRefMsg" class="px-3 py-1.5 rounded text-xs"
                :class="authorRefMsg.startsWith('✅') ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'">
                {{ authorRefMsg }}
              </div>
            </Transition>
            <div class="flex items-center gap-2">
              <label class="text-xs text-[var(--color-ink-light)] whitespace-nowrap">Embedding</label>
              <select v-model="authorRefEmbConfig" class="border border-[var(--color-parchment-darker)] rounded-md px-2 py-1 text-sm max-w-[200px]">
                <option v-for="c in configStore.embeddingChoices" :key="c" :value="c">{{ c }}</option>
              </select>
            </div>
            <input type="file" accept=".txt" multiple @change="onAuthorRefFile" class="text-sm text-[var(--color-ink)]" />
            <div class="flex gap-2">
              <button @click="importAuthorRef" :disabled="authorRefImporting || !authorRefFiles.length || !authorRefEmbConfig"
                class="px-3 py-1.5 rounded-md text-sm font-semibold disabled:opacity-50"
                style="background-color: var(--color-leather); color: var(--color-parchment)" type="button">
                {{ authorRefImporting ? '导入中…' : '▶ 导入参考库' }}
              </button>
              <button v-if="authorRefExists" @click="clearAuthorRef"
                class="px-3 py-1.5 rounded-md text-sm border border-red-200 text-red-600 hover:bg-red-50 transition-colors" type="button">
                清空参考库
              </button>
            </div>
          </div>
        </details>

        <div class="flex justify-end">
          <button @click="saveStyle" class="px-4 py-2 rounded-md text-sm font-semibold" style="background-color: var(--color-leather); color: var(--color-parchment)" type="button">
            保存文风
          </button>
        </div>
      </div>
    </div>

    <!-- 迭代校准 -->
    <div v-if="selectedStyle" class="rounded-xl border border-[var(--color-parchment-darker)] bg-white p-5 space-y-4">
      <h3 class="font-semibold text-[var(--color-leather)]">迭代校准（图灵盲测）</h3>
      <p class="text-sm text-[var(--color-ink-light)]">
        对「{{ selectedStyle }}」的风格指令进行迭代优化：自动生成测试文本，与参考样本混合后图灵盲测（双次正反序），判别器无法识别仿写即为通过。
      </p>
      <div class="flex items-center gap-3">
        <label class="text-xs text-[var(--color-ink-light)] whitespace-nowrap">最大轮次</label>
        <input v-model.number="calibrateMaxIter" type="number" min="1" max="10"
          class="w-20 border border-[var(--color-parchment-darker)] rounded-md px-2 py-1 text-sm" />
        <div class="flex-1" />
        <button v-if="hasCalibrationSnapshot" @click="doRollback"
          class="border border-orange-300 text-orange-600 rounded-md px-3 py-2 text-sm hover:bg-orange-50 transition-colors" type="button">
          回滚校准{{ snapshotTimestamp ? `（${snapshotTimestamp.slice(0, 16)}）` : '' }}
        </button>
        <button @click="doCalibrate" :disabled="calibrateState.running || !analyzeLLM || !selectedStyle"
          class="px-4 py-2 rounded-md text-sm font-semibold disabled:opacity-50"
          style="background-color: var(--color-leather); color: var(--color-parchment)" type="button">
          {{ calibrateState.running ? '校准中…' : '▶ 迭代校准' }}
        </button>
      </div>
      <StreamOutput v-bind="calibrateState" placeholder="校准进度与结果将在此显示…" />
    </div>

    <!-- 叙事DNA章节指令迭代校准 -->
    <div v-if="selectedStyle" class="rounded-xl border border-[var(--color-parchment-darker)] bg-white p-5 space-y-4">
      <h3 class="font-semibold text-[var(--color-leather)]">叙事DNA迭代校准（图灵盲测）</h3>
      <p class="text-sm text-[var(--color-ink-light)]">
        对「{{ selectedStyle }}」的章节指令进行迭代优化：自动生成测试文本，与参考样本混合后图灵盲测叙事模式（推进节奏、场景结构、对话风格等），判别器无法识别仿写即为通过。
      </p>
      <div class="flex items-center gap-3">
        <label class="text-xs text-[var(--color-ink-light)] whitespace-nowrap">最大轮次</label>
        <input v-model.number="narrativeCalibrateMaxIter" type="number" min="1" max="10"
          class="w-20 border border-[var(--color-parchment-darker)] rounded-md px-2 py-1 text-sm" />
        <div class="flex-1" />
        <button v-if="hasCalibrationSnapshot" @click="doRollback"
          class="border border-orange-300 text-orange-600 rounded-md px-3 py-2 text-sm hover:bg-orange-50 transition-colors" type="button">
          回滚校准{{ snapshotTimestamp ? `（${snapshotTimestamp.slice(0, 16)}）` : '' }}
        </button>
        <button @click="doCalibrateNarrative" :disabled="narrativeCalibrateState.running || !analyzeLLM || !selectedStyle"
          class="px-4 py-2 rounded-md text-sm font-semibold disabled:opacity-50"
          style="background-color: var(--color-leather); color: var(--color-parchment)" type="button">
          {{ narrativeCalibrateState.running ? '校准中…' : '▶ 叙事迭代校准' }}
        </button>
      </div>
      <StreamOutput v-bind="narrativeCalibrateState" placeholder="叙事校准进度与结果将在此显示…" />
    </div>

    <!-- 分析新文风 -->
    <div class="rounded-xl border border-[var(--color-parchment-darker)] bg-white p-5 space-y-4">
      <h3 class="font-semibold text-[var(--color-leather)]">分析新文风</h3>
      <div>
        <label class="block text-xs text-[var(--color-ink-light)] mb-1">文风名称</label>
        <input v-model="newStyleName" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm max-w-xs" />
      </div>
      <div>
        <label class="block text-xs text-[var(--color-ink-light)] mb-1">样本文本（前5000字有效）</label>
        <textarea v-model="sampleText" rows="6" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm font-mono resize-y" />
      </div>
      <div class="flex justify-end">
        <button @click="doAnalyze" :disabled="analyzeState.running || !analyzeLLM || !newStyleName || !sampleText"
          class="px-4 py-2 rounded-md text-sm font-semibold disabled:opacity-50" style="background-color: var(--color-leather); color: var(--color-parchment)" type="button">
          {{ analyzeState.running ? '分析中…' : '▶ 分析文风' }}
        </button>
      </div>
      <StreamOutput v-bind="analyzeState" placeholder="分析结果将在此显示…" />
    </div>

    <!-- 叙事DNA -->
    <div class="rounded-xl border border-[var(--color-parchment-darker)] bg-white p-5 space-y-4">
      <h3 class="font-semibold text-[var(--color-leather)]">叙事DNA分析</h3>
      <p class="text-sm text-[var(--color-ink-light)]">为已有文风模板分析叙事DNA（架构/蓝图/章节分层指令）。</p>
      <div class="flex gap-3 flex-wrap">
        <div class="flex-1">
          <label class="block text-xs text-[var(--color-ink-light)] mb-1">目标文风</label>
          <select v-model="selectedStyle" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm">
            <option value="">— 选择文风 —</option>
            <option v-for="s in styleList" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
      </div>
      <div>
        <label class="block text-xs text-[var(--color-ink-light)] mb-1">样本文本（前5000字有效）</label>
        <textarea v-model="dnaSampleText" rows="6" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm font-mono resize-y" />
      </div>
      <div class="flex justify-end">
        <button @click="doAnalyzeDNA" :disabled="dnaState.running || !analyzeLLM || !selectedStyle || !dnaSampleText"
          class="px-4 py-2 rounded-md text-sm font-semibold disabled:opacity-50" style="background-color: var(--color-leather); color: var(--color-parchment)" type="button">
          {{ dnaState.running ? '分析中…' : '▶ 分析叙事DNA' }}
        </button>
      </div>
      <StreamOutput v-bind="dnaState" placeholder="叙事DNA分析结果…" />
    </div>

    <!-- 融合文风 -->
    <div class="rounded-xl border border-[var(--color-parchment-darker)] bg-white p-5 space-y-4">
      <h3 class="font-semibold text-[var(--color-leather)]">融合文风</h3>
      <div>
        <label class="block text-xs text-[var(--color-ink-light)] mb-1">融合后名称</label>
        <input v-model="mergeName" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm max-w-xs" />
      </div>
      <div>
        <label class="block text-xs text-[var(--color-ink-light)] mb-2">选择参与融合的文风（至少2个）</label>
        <div class="flex flex-wrap gap-2">
          <label v-for="s in styleList" :key="s" class="flex items-center gap-1.5 cursor-pointer text-sm select-none">
            <input type="checkbox" :value="s" v-model="mergeSelected" class="accent-[var(--color-leather)]" />
            {{ s }}
          </label>
        </div>
      </div>
      <div>
        <label class="block text-xs text-[var(--color-ink-light)] mb-1">融合偏好（可选）</label>
        <input v-model="mergePreference" placeholder="例如：偏向某某作者风格…" class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm" />
      </div>
      <div class="flex justify-end">
        <button @click="doMerge" :disabled="mergeState.running || mergeSelected.length < 2 || !mergeName"
          class="px-4 py-2 rounded-md text-sm font-semibold disabled:opacity-50" style="background-color: var(--color-leather); color: var(--color-parchment)" type="button">
          {{ mergeState.running ? '融合中…' : '▶ 融合文风' }}
        </button>
      </div>
      <StreamOutput v-bind="mergeState" placeholder="融合结果将在此显示…" />
    </div>
  </div>
</template>
