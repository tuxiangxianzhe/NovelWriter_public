import { ref, computed, onMounted, onActivated, onDeactivated, watch } from 'vue'
import { useProjectStore } from '@/stores/project'
import { useConfigStore } from '@/stores/config'
import { useGenerateStore } from '@/stores/generate'
import { postSSE, generateApi, stylesApi, type SSEHandle } from '@/api/client'

export type StepState = {
  running: boolean
  progress: string
  result: string
  error: string
  progressValue?: number
  sseHandle?: { abort: () => void } | null
}

export const mkState = (): StepState => ({
  running: false, progress: '', result: '', error: '', progressValue: undefined, sseHandle: null,
})

export function useWorkshopState() {
  const projectStore = useProjectStore()
  const configStore = useConfigStore()
  const generateStore = useGenerateStore()

  const llmConfig = ref('')
  const embConfig = ref('')
  const filepath = computed(() => projectStore.filepath)

  // ── 小说参数 ──────────────────────────────────────────────────────────────
  const topic = ref('')
  const genre = ref('玄幻')
  const numChapters = ref(10)
  const wordNumber = ref(3000)
  const userGuidance = ref('')
  const xpType = ref('')
  const xpSelectedPresets = ref<string[]>([])
  const numCharacters = ref('3-6')
  const contNumCharacters = ref('1-3')

  // ── 文风/DNA 列表 ─────────────────────────────────────────────────────────
  const styleList = ref<string[]>([])
  const archStyle = ref('')
  const bpStyle = ref('')
  const chStyle = ref('')
  const chNarrativeStyle = ref('')
  const contStyle = ref('')

  // ── 步骤状态 ──────────────────────────────────────────────────────────────
  const arch = ref(mkState())
  const bp = ref(mkState())
  const chapter = ref(mkState())
  const finalize = ref(mkState())
  const expand = ref(mkState())

  // 分步架构
  const stepMode = ref(false)
  const stepSeed = ref(mkState())
  const stepChar = ref(mkState())
  const stepCharState = ref(mkState())
  const stepWorld = ref(mkState())
  const stepPlot = ref(mkState())
  const seedText = ref('')
  const charText = ref('')
  const charStateText = ref('')
  const worldText = ref('')
  const plotText = ref('')

  // 修订相关
  const revisionGuidance = ref({
    core_seed: '', characters: '', char_state: '', world: '', plot: '',
    cont_seed: '', cont_world: '', cont_chars: '', cont_arcs: '', cont_char_state: '',
  })
  const revisionState = ref({
    core_seed: mkState(), characters: mkState(), char_state: mkState(), world: mkState(), plot: mkState(),
    cont_seed: mkState(), cont_world: mkState(), cont_chars: mkState(), cont_arcs: mkState(), cont_char_state: mkState(),
  })

  const revisionContext = ref({
    include_core_seed: false, include_characters: false,
    include_world_building: false, include_plot: false,
  })

  // 注入选项
  const injectCharToWorld = ref(false)
  // 章节参数
  const injectWorldBuilding = ref(false)
  const chapterNum = ref(1)
  const charactersInvolved = ref('')
  const keyItems = ref('')
  const sceneLocation = ref('')
  const timeConstraint = ref('')
  const chGuidance = ref('')

  // 一键生成
  const batch = ref(mkState())

  // 续写
  const continueArch = ref(mkState())
  const newChapters = ref(5)
  const continueGuidance = ref('')
  const contXpType = ref('')
  const compressRunning = ref(false)
  const compressResult = ref('')
  const compressWorldBuilding = ref(true)

  // 续写分步
  const contStepMode = ref(false)
  const contStepSeed = ref(mkState())
  const contSeedText = ref('')
  const contStepWorld = ref(mkState())
  const contWorldText = ref('')
  const contStepChars = ref(mkState())
  const contStepArcs = ref(mkState())
  const contStepCharState = ref(mkState())
  const contCharsText = ref('')
  const contArcsText = ref('')
  const contCharStateText = ref('')

  // 补充角色
  const supplementChar = ref(mkState())
  const supplementGuidance = ref('')
  const supplementNum = ref('1-2')
  const supplementResult = ref('')
  const contSupplementChar = ref(mkState())
  const contSupplementGuidance = ref('')
  const contSupplementNum = ref('1-2')
  const contSupplementResult = ref('')

  // 角色动力学
  const characterDynamicsContent = ref('')

  // 润色
  const polishGuidance = ref('')
  const expandOriginal = ref('')   // 润色前原文
  const expandNew = ref('')        // 润色后新文
  const expandChapterNum = ref(0)  // 润色的章节号

  // 去 AI 痕迹
  const humanize = ref(mkState())
  const humanizerBatch = ref(false)
  const humanizerR8 = ref(false)
  const humanizerFocus = ref('')
  const humanizerStart = ref(1)
  const humanizerEnd = ref(1)
  const humanizerDepth = ref<'quick' | 'standard' | 'deep'>('standard')
  // 对比预览状态
  const humanizerOriginal = ref('')
  const humanizerHumanized = ref('')
  const humanizerChanges = ref('')
  const humanizerPreviewTab = ref<'humanized' | 'original' | 'changes'>('humanized')
  const humanizerPending = ref(false)       // 有待确认的结果
  const humanizerSaving = ref(false)
  const humanizerChapterNum = ref(0)        // 处理的章节号

  // 导出
  const exporting = ref(false)

  // 保存消息
  const saveMsg = ref('')

  // 重载
  const reloading = ref(false)

  // ── 生命周期 ──────────────────────────────────────────────────────────────
  onMounted(async () => {
    await projectStore.loadActive()
    await Promise.all([configStore.loadAll(), generateStore.loadStatus()])
    arch.value.result = generateStore.architectureContent
    bp.value.result = generateStore.blueprintContent
    characterDynamicsContent.value = generateStore.characterDynamicsContent
    // 从独立文件填充步骤字段（优先于项目数据中的缓存值）
    if (generateStore.coreSeedContent) seedText.value = generateStore.coreSeedContent
    if (generateStore.characterDynamicsContent) charText.value = generateStore.characterDynamicsContent
    if (generateStore.worldBuildingContent) worldText.value = generateStore.worldBuildingContent
    if (generateStore.plotArchitectureContent) plotText.value = generateStore.plotArchitectureContent
    if (generateStore.characterStateContent) charStateText.value = generateStore.characterStateContent
    if (projectStore.activeProjectData) {
      const p = projectStore.activeProjectData
      topic.value = p.topic ?? ''
      genre.value = p.genre ?? '玄幻'
      numChapters.value = p.num_chapters ?? 10
      wordNumber.value = p.word_number ?? 3000
      userGuidance.value = p.user_guidance ?? ''
      xpType.value = p.xp_type ?? ''
      xpSelectedPresets.value = p.xp_selected_presets ?? []
      if (p.arch_style) archStyle.value = p.arch_style
      if (p.bp_style) bpStyle.value = p.bp_style
      if (p.ch_style) chStyle.value = p.ch_style
      if (p.ch_narrative_style) chNarrativeStyle.value = p.ch_narrative_style
      if (p.cont_style) contStyle.value = p.cont_style
      if (p.cont_xp_type) contXpType.value = p.cont_xp_type
      if (p.step_seed_text) seedText.value = p.step_seed_text
      if (p.step_char_text) charText.value = p.step_char_text
      if (p.step_char_state_text) charStateText.value = p.step_char_state_text
      if (p.step_world_text) worldText.value = p.step_world_text
      if (p.step_plot_text) plotText.value = p.step_plot_text
      if (p.continue_guidance) continueGuidance.value = p.continue_guidance
      if (p.cont_new_chapters) newChapters.value = p.cont_new_chapters
      if (p.cont_step_chars_text) contCharsText.value = p.cont_step_chars_text
      if (p.cont_step_arcs_text) contArcsText.value = p.cont_step_arcs_text
      if (p.cont_step_char_state_text) contCharStateText.value = p.cont_step_char_state_text
    }
    try {
      const res = await stylesApi.list()
      styleList.value = ['不使用文风', ...res.data.styles]
    } catch { /* ignore */ }
    const p = projectStore.activeProjectData
    if (p?.llm_config_name && configStore.llmChoices.includes(p.llm_config_name)) {
      llmConfig.value = p.llm_config_name
    } else if (configStore.llmChoices.length) {
      llmConfig.value = configStore.llmChoices[0]
    }
    if (p?.emb_config_name && configStore.embeddingChoices.includes(p.emb_config_name)) {
      embConfig.value = p.emb_config_name
    } else if (configStore.embeddingChoices.length) {
      embConfig.value = configStore.embeddingChoices[0]
    }
  })

  // ── 加载/重载项目内容 ─────────────────────────────────────────────────────
  async function reloadProjectContent() {
    reloading.value = true
    try {
      await projectStore.loadActive()
      const p = projectStore.activeProjectData
      if (p) {
        topic.value = p.topic ?? ''
        genre.value = p.genre ?? '玄幻'
        numChapters.value = p.num_chapters ?? 10
        wordNumber.value = p.word_number ?? 3000
        userGuidance.value = p.user_guidance ?? ''
        xpType.value = p.xp_type ?? ''
        xpSelectedPresets.value = p.xp_selected_presets ?? []
        if (p.llm_config_name && configStore.llmChoices.includes(p.llm_config_name)) {
          llmConfig.value = p.llm_config_name
        }
        if (p.emb_config_name && configStore.embeddingChoices.includes(p.emb_config_name)) {
          embConfig.value = p.emb_config_name
        }
        archStyle.value = p.arch_style || ''
        bpStyle.value = p.bp_style || ''
        chStyle.value = p.ch_style || ''
        chNarrativeStyle.value = p.ch_narrative_style || ''
        contStyle.value = p.cont_style || ''
        contXpType.value = p.cont_xp_type || ''
        seedText.value = p.step_seed_text || ''
        charText.value = p.step_char_text || ''
        charStateText.value = p.step_char_state_text || ''
        worldText.value = p.step_world_text || ''
        plotText.value = p.step_plot_text || ''
        continueGuidance.value = p.continue_guidance || ''
        newChapters.value = p.cont_new_chapters ?? 5
        contSeedText.value = p.cont_step_seed_text || ''
        contWorldText.value = p.cont_step_world_text || ''
        contCharsText.value = p.cont_step_chars_text || ''
        contArcsText.value = p.cont_step_arcs_text || ''
        contCharStateText.value = p.cont_step_char_state_text || ''
      }
      await generateStore.loadStatus()
      arch.value.result = generateStore.architectureContent
      bp.value.result = generateStore.blueprintContent
      characterDynamicsContent.value = generateStore.characterDynamicsContent
      // 从独立文件刷新步骤字段
      if (generateStore.coreSeedContent) seedText.value = generateStore.coreSeedContent
      if (generateStore.characterDynamicsContent) charText.value = generateStore.characterDynamicsContent
      if (generateStore.worldBuildingContent) worldText.value = generateStore.worldBuildingContent
      if (generateStore.plotArchitectureContent) plotText.value = generateStore.plotArchitectureContent
      if (generateStore.characterStateContent) charStateText.value = generateStore.characterStateContent
    } finally {
      reloading.value = false
    }
  }

  // 切换项目时自动重载
  watch(() => projectStore.activeProject, (name) => {
    if (autoSaveTimer) { clearTimeout(autoSaveTimer); autoSaveTimer = null }
    if (!name) return
    reloadProjectContent()
  })

  // ── 基础参数自动保存 ──────────────────────────────────────────────────────
  let autoSaveTimer: ReturnType<typeof setTimeout> | null = null

  function scheduleAutoSave() {
    if (!projectStore.activeProject) return
    if (autoSaveTimer) clearTimeout(autoSaveTimer)
    const targetProject = projectStore.activeProject
    autoSaveTimer = setTimeout(() => {
      if (projectStore.activeProject !== targetProject) return
      projectStore.saveProject({
        topic: topic.value,
        genre: genre.value,
        num_chapters: numChapters.value,
        word_number: wordNumber.value,
        user_guidance: userGuidance.value,
        xp_type: xpType.value,
        xp_selected_presets: xpSelectedPresets.value,
        llm_config_name: llmConfig.value,
        emb_config_name: embConfig.value,
        arch_style: archStyle.value,
        bp_style: bpStyle.value,
        ch_style: chStyle.value,
        ch_narrative_style: chNarrativeStyle.value,
        cont_style: contStyle.value,
        cont_xp_type: contXpType.value,
        step_seed_text: seedText.value,
        step_char_text: charText.value,
        step_char_state_text: charStateText.value,
        step_world_text: worldText.value,
        step_plot_text: plotText.value,
        continue_guidance: continueGuidance.value,
        cont_new_chapters: newChapters.value,
        cont_step_seed_text: contSeedText.value,
        cont_step_world_text: contWorldText.value,
        cont_step_chars_text: contCharsText.value,
        cont_step_arcs_text: contArcsText.value,
        cont_step_char_state_text: contCharStateText.value,
      })
    }, 1500)
  }

  watch([topic, genre, numChapters, wordNumber, userGuidance, xpType, xpSelectedPresets,
         llmConfig, embConfig, archStyle, bpStyle, chStyle, chNarrativeStyle,
         contStyle, contXpType,
         seedText, charText, charStateText, worldText, plotText,
         continueGuidance, newChapters, contSeedText, contWorldText, contCharsText, contArcsText, contCharStateText], scheduleAutoSave)

  // ── 辅助 ──────────────────────────────────────────────────────────────────
  function runSSE(state: StepState, url: string, body: Record<string, unknown>) {
    state.running = true
    state.progress = ''
    state.result = ''
    state.error = ''
    state.progressValue = undefined
    const handle = postSSE(
      url, body,
      (msg, value, content) => {
        state.progress = msg
        if (value !== undefined) state.progressValue = value
        // 流式输出：progress 事件携带的 content 实时显示在结果区域
        if (content) state.result = content
      },
      (content) => { state.result = content },
      (err) => { state.error = err; state.running = false },
      () => { state.running = false; state.sseHandle = null },
    )
    state.sseHandle = handle
  }

  function cancelSSE(state: StepState) {
    if (state.sseHandle) {
      state.sseHandle.abort()
      state.sseHandle = null
    }
  }

  function runStepSSE(state: StepState, textRef: { value: string }, url: string, body: Record<string, unknown>) {
    state.running = true
    state.progress = ''
    state.result = ''
    state.error = ''
    state.progressValue = undefined
    const handle = postSSE(
      url, body,
      (msg, value) => { state.progress = msg; if (value !== undefined) state.progressValue = value },
      (content) => { state.result = content; textRef.value = content },
      (err) => { state.error = err; state.running = false },
      () => { state.running = false; state.sseHandle = null },
    )
    state.sseHandle = handle
  }

  // ── 保存 ──────────────────────────────────────────────────────────────────
  async function saveArchitecture() {
    // 已废弃：架构文件现在是只读组装副本
    saveMsg.value = '架构文件为只读，请使用各组件的独立保存按钮'
    setTimeout(() => { saveMsg.value = '' }, 3000)
  }

  async function saveComponent(name: string, content: string) {
    if (!content) return
    try {
      const res = await generateApi.saveComponent(name, content, filepath.value)
      saveMsg.value = `✅ ${name} 已保存`
      if (res.data.assembled_content) {
        arch.value.result = res.data.assembled_content
      }
    } catch (e: unknown) { saveMsg.value = `❌ ${(e as Error).message}` }
    setTimeout(() => { saveMsg.value = '' }, 3000)
  }

  async function saveCoreSeed() { await saveComponent('core_seed', seedText.value) }
  async function saveCharDynamics() { await saveComponent('character_dynamics', charText.value) }
  async function saveCharState() { await saveComponent('character_state', charStateText.value) }
  async function saveWorldBuilding() { await saveComponent('world_building', worldText.value) }
  async function savePlotArch() { await saveComponent('plot_architecture', plotText.value) }

  async function saveBlueprint() {
    try {
      await generateApi.saveBlueprint(bp.value.result, filepath.value)
      saveMsg.value = '✅ 蓝图已保存'
    } catch (e: unknown) { saveMsg.value = `❌ ${(e as Error).message}` }
    setTimeout(() => { saveMsg.value = '' }, 3000)
  }

  async function saveCharacterDynamics() {
    if (!characterDynamicsContent.value) return
    try {
      await generateApi.saveCharacterDynamics(characterDynamicsContent.value, filepath.value)
      saveMsg.value = '✅ 角色动力学已保存'
    } catch (e: unknown) { saveMsg.value = `❌ ${(e as Error).message}` }
    setTimeout(() => { saveMsg.value = '' }, 3000)
  }

  async function saveChapter() {
    if (!chapter.value.result) return
    try {
      await generateApi.saveChapter(chapterNum.value, chapter.value.result, filepath.value)
      saveMsg.value = `✅ 第 ${chapterNum.value} 章已保存`
    } catch (e: unknown) { saveMsg.value = `❌ ${(e as Error).message}` }
    setTimeout(() => { saveMsg.value = '' }, 3000)
  }

  // ── Ctrl+S 快捷键 ────────────────────────────────────────────────────────
  function handleKeydown(e: KeyboardEvent) {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault()
      if (chapter.value.result && !chapter.value.running) saveChapter()
      else if (bp.value.result && !bp.value.running) saveBlueprint()
      else if (arch.value.result && !arch.value.running) saveArchitecture()
    }
  }
  onActivated(() => document.addEventListener('keydown', handleKeydown))
  onDeactivated(() => document.removeEventListener('keydown', handleKeydown))

  // ── Step 1: 架构 ─────────────────────────────────────────────────────────
  function doGenerateArch() {
    const s = arch.value
    s.running = true; s.progress = ''; s.result = ''; s.error = ''; s.progressValue = undefined
    const handle = postSSE(
      '/generate/architecture',
      {
        llm_config_name: llmConfig.value,
        topic: topic.value, genre: genre.value,
        num_chapters: numChapters.value, word_number: wordNumber.value,
        filepath: filepath.value, user_guidance: userGuidance.value,
        arch_style_name: archStyle.value === '不使用文风' ? null : archStyle.value || null,
        xp_type: xpType.value,
        num_characters: numCharacters.value,
      },
      (msg, value) => { s.progress = msg; if (value !== undefined) s.progressValue = value },
      (content) => {
        try {
          const data = JSON.parse(content)
          seedText.value = data.core_seed ?? ''
          charText.value = data.character_dynamics ?? ''
          worldText.value = data.world_building ?? ''
          plotText.value = data.plot_architecture ?? ''
          charStateText.value = data.character_state ?? ''
          s.result = data.assembled ?? content
        } catch {
          s.result = content
        }
      },
      (err) => { s.error = err; s.running = false },
      () => { s.running = false; s.sseHandle = null },
    )
    s.sseHandle = handle
  }

  function doStepSeed() {
    runStepSSE(stepSeed.value, seedText, '/generate/architecture/step/core_seed', {
      llm_config_name: llmConfig.value,
      topic: topic.value, genre: genre.value,
      num_chapters: numChapters.value, word_number: wordNumber.value,
      step_guidance: '', global_guidance: userGuidance.value, xp_type: xpType.value,
    })
  }
  function doStepChar() {
    runStepSSE(stepChar.value, charText, '/generate/architecture/step/characters', {
      llm_config_name: llmConfig.value,
      seed_text: seedText.value,
      step_guidance: '', global_guidance: userGuidance.value, xp_type: xpType.value,
      num_characters: numCharacters.value,
    })
  }
  function doSupplementChar() {
    runStepSSE(supplementChar.value, supplementResult, '/generate/architecture/supplement_characters', {
      llm_config_name: llmConfig.value,
      existing_characters: charText.value,
      supplement_guidance: supplementGuidance.value,
      num_characters: supplementNum.value,
      core_seed: seedText.value,
      world_building: worldText.value,
      filepath: filepath.value,
    })
  }
  function appendSupplementChar() {
    if (supplementResult.value.trim()) {
      charText.value = charText.value.trimEnd() + '\n\n' + supplementResult.value.trim()
      supplementResult.value = ''
      supplementGuidance.value = ''
    }
  }
  function doStepCharState() {
    runStepSSE(stepCharState.value, charStateText, '/generate/architecture/step/char_state', {
      llm_config_name: llmConfig.value,
      char_dynamics_text: charText.value,
    })
  }
  function doStepWorld() {
    runStepSSE(stepWorld.value, worldText, '/generate/architecture/step/world', {
      llm_config_name: llmConfig.value,
      seed_text: seedText.value,
      step_guidance: '', global_guidance: userGuidance.value, xp_type: xpType.value,
      char_text: injectCharToWorld.value ? charText.value : '',
    })
  }
  function doStepPlot() {
    runStepSSE(stepPlot.value, plotText, '/generate/architecture/step/plot', {
      llm_config_name: llmConfig.value,
      seed_text: seedText.value, char_text: charText.value, world_text: worldText.value,
      step_guidance: '', global_guidance: userGuidance.value,
      num_chapters: numChapters.value, arch_style_name: archStyle.value || null,
      xp_type: xpType.value,
    })
  }

  function doRevise(stepType: string) {
    const textRefs: Record<string, { value: string }> = {
      core_seed: seedText, characters: charText, char_state: charStateText,
      world: worldText, plot: plotText,
      cont_seed: contSeedText, cont_world: contWorldText, cont_chars: contCharsText,
      cont_arcs: contArcsText, cont_char_state: contCharStateText,
    }
    // Map to backend step_type labels
    const backendStepType: Record<string, string> = {
      core_seed: 'core_seed', characters: 'characters', char_state: 'char_state',
      world: 'world', plot: 'plot',
      cont_seed: 'core_seed', cont_world: 'world', cont_chars: 'characters',
      cont_arcs: 'plot', cont_char_state: 'char_state',
    }
    const textRef = textRefs[stepType]
    const state = (revisionState.value as Record<string, StepState>)[stepType]
    const guidance = (revisionGuidance.value as Record<string, string>)[stepType]
    if (!textRef?.value || !guidance) return
    runStepSSE(state, textRef, generateApi.reviseStep(), {
      llm_config_name: llmConfig.value,
      original_content: textRef.value,
      revision_guidance: guidance,
      step_type: backendStepType[stepType] || stepType,
      filepath: filepath.value,
      include_core_seed: revisionContext.value.include_core_seed,
      include_characters: revisionContext.value.include_characters,
      include_world_building: revisionContext.value.include_world_building,
      include_plot: revisionContext.value.include_plot,
    })
  }

  async function doAssemble() {
    try {
      const res = await generateApi.assembleArch({
        filepath: filepath.value, topic: topic.value, genre: genre.value,
        num_chapters: numChapters.value, word_number: wordNumber.value,
        seed_text: seedText.value, char_text: charText.value,
        char_state_text: charStateText.value, world_text: worldText.value,
        plot_text: plotText.value,
      })
      arch.value.result = res.data.content
    } catch (e: unknown) {
      arch.value.error = (e as Error).message
    }
  }

  // ── Step 2: 蓝图 ─────────────────────────────────────────────────────────
  function doGenerateBP() {
    runSSE(bp.value, '/generate/blueprint', {
      llm_config_name: llmConfig.value, filepath: filepath.value,
      num_chapters: numChapters.value, user_guidance: userGuidance.value,
      bp_style_name: bpStyle.value === '不使用文风' ? null : bpStyle.value || null,
      xp_type: xpType.value,
    })
  }

  // ── Step 3: 章节 ─────────────────────────────────────────────────────────
  function doGenerateChapter() {
    runSSE(chapter.value, '/generate/chapter', {
      llm_config_name: llmConfig.value, emb_config_name: embConfig.value,
      filepath: filepath.value, chapter_num: chapterNum.value,
      word_number: wordNumber.value,
      user_guidance: chGuidance.value || userGuidance.value,
      characters_involved: charactersInvolved.value,
      key_items: keyItems.value, scene_location: sceneLocation.value,
      time_constraint: timeConstraint.value,
      style_name: chStyle.value === '不使用文风' ? null : chStyle.value || null,
      narrative_style_name: chNarrativeStyle.value === '不使用文风' ? null : chNarrativeStyle.value || null,
      xp_type: xpType.value,
      inject_world_building: injectWorldBuilding.value,
    })
  }

  // ── Step 4: 精炼 ─────────────────────────────────────────────────────────
  function doFinalize() {
    runSSE(finalize.value, '/generate/finalize', {
      llm_config_name: llmConfig.value, emb_config_name: embConfig.value,
      filepath: filepath.value, chapter_num: chapterNum.value,
      word_number: wordNumber.value,
    })
  }

  // ── 一键完成 ──────────────────────────────────────────────────────────────
  watch(() => batch.value.running, (running, wasRunning) => {
    if (wasRunning && !running && batch.value.result && !batch.value.error) {
      doExportNovel()
    }
  })

  function doBatchGenerate() {
    runSSE(batch.value, '/generate/batch', {
      llm_config_name: llmConfig.value, emb_config_name: embConfig.value,
      filepath: filepath.value, word_number: wordNumber.value,
      user_guidance: userGuidance.value,
      style_name: chStyle.value === '不使用文风' ? null : chStyle.value || null,
      narrative_style_name: chNarrativeStyle.value === '不使用文风' ? null : chNarrativeStyle.value || null,
      xp_type: xpType.value,
      inject_world_building: injectWorldBuilding.value,
    })
  }

  // ── Step 5: 润色 ─────────────────────────────────────────────────────────
  function doExpand() {
    // 清空上次的对比结果
    expandOriginal.value = ''
    expandNew.value = ''
    expandChapterNum.value = chapterNum.value
    const s = expand.value
    s.running = true; s.progress = ''; s.result = ''; s.error = ''; s.progressValue = undefined
    const handle = postSSE(
      '/generate/expand',
      {
        llm_config_name: llmConfig.value, filepath: filepath.value,
        chapter_num: chapterNum.value,
        style_name: chStyle.value === '不使用文风' ? null : chStyle.value || null,
        narrative_style_name: chNarrativeStyle.value === '不使用文风' ? null : chNarrativeStyle.value || null,
        xp_type: xpType.value, polish_guidance: polishGuidance.value,
      },
      (msg, value, content) => {
        s.progress = msg
        if (value !== undefined) s.progressValue = value
        if (content) s.result = content
      },
      (content) => {
        // 完成回调：解析 JSON 响应
        s.result = content
        const marker = '<!--EXPAND_JSON-->'
        if (content.startsWith(marker)) {
          try {
            const data = JSON.parse(content.slice(marker.length))
            expandOriginal.value = data.original || ''
            expandNew.value = data.expanded || ''
            expandChapterNum.value = data.chapter_num || chapterNum.value
            s.result = '' // 清空 result，用 expandNew 展示
          } catch { /* 解析失败则保持原样 */ }
        }
      },
      (err) => { s.error = err; s.running = false },
      () => { s.running = false; s.sseHandle = null },
    )
    s.sseHandle = handle
  }

  async function saveExpandResult(useNew: boolean) {
    const num = expandChapterNum.value
    const content = useNew ? expandNew.value : expandOriginal.value
    if (!num || !content) return
    try {
      await generateApi.saveChapter(num, content, filepath.value)
      saveMsg.value = `✅ 第${num}章已保存（${useNew ? '新版' : '旧版'}）`
    } catch (e: unknown) {
      saveMsg.value = `❌ ${(e as Error).message}`
    }
    setTimeout(() => { saveMsg.value = '' }, 3000)
  }

  // ── Step 6: 去 AI 痕迹 ─────────────────────────────────────────────────
  function _resetHumanizerPreview() {
    humanizerOriginal.value = ''
    humanizerHumanized.value = ''
    humanizerChanges.value = ''
    humanizerPending.value = false
    humanizerPreviewTab.value = 'humanized'
    humanizerChapterNum.value = 0
  }

  function doHumanize() {
    _resetHumanizerPreview()
    const s = humanize.value
    s.running = true; s.progress = ''; s.result = ''; s.error = ''; s.progressValue = undefined
    const handle = postSSE(
      '/generate/humanize',
      {
        llm_config_name: llmConfig.value,
        filepath: filepath.value,
        chapter_num: chapterNum.value,
        enable_r8: humanizerR8.value,
        user_focus: humanizerFocus.value,
        depth: humanizerDepth.value,
      },
      (msg, value) => { s.progress = msg; if (value !== undefined) s.progressValue = value },
      (content) => {
        s.result = content
        // 解析 JSON 结果，填充对比预览
        try {
          const data = JSON.parse(content)
          humanizerOriginal.value = data.original ?? ''
          humanizerHumanized.value = data.humanized ?? ''
          humanizerChanges.value = data.changes ?? ''
          humanizerChapterNum.value = data.chapter_num ?? chapterNum.value
          humanizerPending.value = true
          humanizerPreviewTab.value = 'humanized'
        } catch {
          // 非 JSON（错误信息等），直接显示
        }
      },
      (err) => { s.error = err; s.running = false },
      () => { s.running = false; s.sseHandle = null },
    )
    s.sseHandle = handle
  }

  function doBatchHumanize() {
    _resetHumanizerPreview()
    runSSE(humanize.value, '/generate/humanize/batch', {
      llm_config_name: llmConfig.value,
      filepath: filepath.value,
      start_chapter: humanizerStart.value,
      end_chapter: humanizerEnd.value,
      enable_r8: humanizerR8.value,
      user_focus: humanizerFocus.value,
      depth: humanizerDepth.value,
    })
  }

  async function doConfirmHumanize(keepHumanized: boolean) {
    const num = humanizerChapterNum.value
    const text = keepHumanized ? humanizerHumanized.value : humanizerOriginal.value
    if (!text || !num) return
    humanizerSaving.value = true
    try {
      await generateApi.saveChapter(num, text, filepath.value)
      humanize.value.result = keepHumanized
        ? `✅ 第 ${num} 章已保存去 AI 后的版本`
        : `✅ 第 ${num} 章已保留原文`
      humanizerPending.value = false
    } catch (e: unknown) {
      humanize.value.error = (e as Error).message
    }
    humanizerSaving.value = false
  }

  // ── 导出 ──────────────────────────────────────────────────────────────────
  async function doExportNovel() {
    exporting.value = true
    try {
      const res = await generateApi.exportNovel(filepath.value)
      const blob = new Blob([res.data], { type: 'text/plain;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'novel_export.txt'
      a.click()
      URL.revokeObjectURL(url)
      saveMsg.value = '✅ 小说已导出'
    } catch (e: unknown) {
      saveMsg.value = `❌ 导出失败: ${(e as Error).message}`
    }
    exporting.value = false
    setTimeout(() => { saveMsg.value = '' }, 3000)
  }

  // ── 续写 ──────────────────────────────────────────────────────────────────
  function doContinueArch() {
    const added = newChapters.value
    const s = continueArch.value
    s.running = true; s.progress = ''; s.result = ''; s.error = ''; s.progressValue = undefined
    const handle = postSSE(
      '/generate/architecture/continue',
      {
        llm_config_name: llmConfig.value, filepath: filepath.value,
        new_chapters: added, user_guidance: continueGuidance.value,
        arch_style_name: contStyle.value === '不使用文风' ? null : contStyle.value || null,
        xp_type: contXpType.value,
        num_characters: contNumCharacters.value,
      },
      (msg, value) => { s.progress = msg; if (value !== undefined) s.progressValue = value },
      (content) => { s.result = content },
      (err) => { s.error = err; s.running = false },
      () => {
        s.running = false; s.sseHandle = null
        if (s.result && !s.error) {
          numChapters.value = numChapters.value + added
          reloadProjectContent()
        }
      },
    )
    s.sseHandle = handle
  }

  // ── 续写分步 ──────────────────────────────────────────────────────────────
  function doContStepSeed() {
    runStepSSE(contStepSeed.value, contSeedText, '/generate/architecture/continue/step/seed', {
      llm_config_name: llmConfig.value, filepath: filepath.value,
      new_chapters: newChapters.value, user_guidance: continueGuidance.value,
      arch_style_name: contStyle.value === '不使用文风' ? null : contStyle.value || null,
      xp_type: contXpType.value,
    })
  }
  function doContStepWorld() {
    runStepSSE(contStepWorld.value, contWorldText, '/generate/architecture/continue/step/world', {
      llm_config_name: llmConfig.value, filepath: filepath.value,
      new_chapters: newChapters.value, user_guidance: continueGuidance.value,
      continuation_seed: contSeedText.value,
      arch_style_name: contStyle.value === '不使用文风' ? null : contStyle.value || null,
      xp_type: contXpType.value,
    })
  }
  function doContStepChars() {
    runStepSSE(contStepChars.value, contCharsText, '/generate/architecture/continue/step/characters', {
      llm_config_name: llmConfig.value, filepath: filepath.value,
      new_chapters: newChapters.value, user_guidance: continueGuidance.value,
      arch_style_name: contStyle.value === '不使用文风' ? null : contStyle.value || null,
      xp_type: contXpType.value,
      num_characters: contNumCharacters.value,
      continuation_seed: contSeedText.value, world_expansion: contWorldText.value,
    })
  }
  function doContSupplementChar() {
    runStepSSE(contSupplementChar.value, contSupplementResult, '/generate/architecture/supplement_characters', {
      llm_config_name: llmConfig.value,
      existing_characters: contCharsText.value,
      supplement_guidance: contSupplementGuidance.value,
      num_characters: contSupplementNum.value,
      core_seed: seedText.value,
      world_building: worldText.value,
      filepath: filepath.value,
    })
  }
  function appendContSupplementChar() {
    if (contSupplementResult.value.trim()) {
      contCharsText.value = contCharsText.value.trimEnd() + '\n\n' + contSupplementResult.value.trim()
      contSupplementResult.value = ''
      contSupplementGuidance.value = ''
    }
  }
  function doContStepArcs() {
    runStepSSE(contStepArcs.value, contArcsText, '/generate/architecture/continue/step/arcs', {
      llm_config_name: llmConfig.value, filepath: filepath.value,
      new_chapters: newChapters.value, user_guidance: continueGuidance.value,
      new_characters_text: contCharsText.value,
      arch_style_name: contStyle.value === '不使用文风' ? null : contStyle.value || null,
      xp_type: contXpType.value,
      continuation_seed: contSeedText.value, world_expansion: contWorldText.value,
    })
  }
  function doContStepCharState() {
    runStepSSE(contStepCharState.value, contCharStateText, '/generate/architecture/continue/step/char_state', {
      llm_config_name: llmConfig.value, filepath: filepath.value,
      new_characters_text: contCharsText.value,
    })
  }
  async function doContAssemble() {
    try {
      const res = await generateApi.assembleContinuation({
        filepath: filepath.value, new_chapters: newChapters.value,
        new_characters_text: contCharsText.value,
        new_arcs_text: contArcsText.value,
        new_char_state_text: contCharStateText.value,
        continuation_seed: contSeedText.value,
        world_expansion: contWorldText.value,
      })
      continueArch.value.result = res.data.content
      if (res.data.new_total_chapters) {
        numChapters.value = res.data.new_total_chapters
      }
    } catch (e: unknown) {
      continueArch.value.error = (e as Error).message
    }
  }

  async function doCompressContext() {
    compressRunning.value = true
    compressResult.value = ''
    try {
      const res = await generateApi.compressContext({
        llm_config_name: llmConfig.value,
        filepath: filepath.value,
        include_world_building: compressWorldBuilding.value,
      })
      compressResult.value = res.data.message
    } catch (e: unknown) {
      compressResult.value = `❌ 压缩失败: ${(e as Error).message}`
    }
    compressRunning.value = false
  }

  return {
    // stores
    projectStore, configStore, generateStore,
    // basic params
    llmConfig, embConfig, filepath,
    topic, genre, numChapters, wordNumber, userGuidance, xpType, xpSelectedPresets, numCharacters, contNumCharacters,
    // styles
    styleList, archStyle, bpStyle, chStyle, chNarrativeStyle, contStyle,
    // step states
    arch, bp, chapter, finalize, expand,
    // step-by-step arch
    stepMode, stepSeed, stepChar, stepCharState, stepWorld, stepPlot,
    seedText, charText, charStateText, worldText, plotText,
    // inject options
    injectCharToWorld,
    // chapter params
    injectWorldBuilding,
    chapterNum, charactersInvolved, keyItems, sceneLocation, timeConstraint, chGuidance,
    // batch
    batch,
    // continue
    continueArch, newChapters, continueGuidance, contXpType,
    // continue step-by-step
    contStepMode,
    contStepSeed, contSeedText, contStepWorld, contWorldText,
    contStepChars, contStepArcs, contStepCharState,
    contCharsText, contArcsText, contCharStateText,
    // supplement characters
    supplementChar, supplementGuidance, supplementNum, supplementResult,
    doSupplementChar, appendSupplementChar,
    contSupplementChar, contSupplementGuidance, contSupplementNum, contSupplementResult,
    doContSupplementChar, appendContSupplementChar,
    // character dynamics
    characterDynamicsContent,
    // polish
    polishGuidance,
    expandOriginal, expandNew, expandChapterNum, saveExpandResult,
    // humanizer
    humanize, humanizerBatch, humanizerR8, humanizerFocus,
    humanizerStart, humanizerEnd, humanizerDepth,
    humanizerOriginal, humanizerHumanized, humanizerChanges,
    humanizerPreviewTab, humanizerPending, humanizerSaving,
    doHumanize, doBatchHumanize, doConfirmHumanize,
    // misc
    exporting, saveMsg, reloading,
    // functions
    reloadProjectContent, cancelSSE,
    saveArchitecture, saveBlueprint, saveChapter, saveCharacterDynamics,
    saveComponent, saveCoreSeed, saveCharDynamics, saveCharState, saveWorldBuilding, savePlotArch,
    revisionGuidance, revisionState, revisionContext, doRevise,
    doGenerateArch, doStepSeed, doStepChar, doStepCharState, doStepWorld, doStepPlot, doAssemble,
    doGenerateBP, doGenerateChapter, doFinalize,
    doBatchGenerate, doExpand, doExportNovel,
    doContinueArch, doContStepSeed, doContStepWorld, doContStepChars, doContStepArcs, doContStepCharState, doContAssemble,
    compressRunning, compressResult, compressWorldBuilding, doCompressContext,
  }
}
