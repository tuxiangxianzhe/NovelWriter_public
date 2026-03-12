import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { projectsApi } from '@/api/client'

export interface Project {
  name: string
  filepath: string
  topic: string
  genre: string
  num_chapters: number
  word_number: number
  user_guidance: string
  xp_type: string
  // 持久化到 project_config.json 的扩展字段
  llm_config_name?: string
  emb_config_name?: string
  arch_style?: string
  bp_style?: string
  ch_style?: string
  ch_narrative_style?: string
  expand_style?: string
  expand_narrative_style?: string
  cont_style?: string
  cont_xp_type?: string
  // 分步生成中间内容（断点续作）
  step_seed_text?: string
  step_char_text?: string
  step_char_state_text?: string
  step_world_text?: string
  step_plot_text?: string
  continue_guidance?: string
  cont_new_chapters?: number
  cont_step_seed_text?: string
  cont_step_world_text?: string
  cont_step_chars_text?: string
  cont_step_arcs_text?: string
  cont_step_char_state_text?: string
  created_at?: string
  updated_at?: string
}

export const useProjectStore = defineStore('project', () => {
  const projects = ref<string[]>([])
  const activeProject = ref<string>('')
  const activeProjectData = ref<Project | null>(null)
  const loading = ref(false)

  const filepath = computed(() => activeProjectData.value?.filepath ?? './output')

  async function loadProjects() {
    const res = await projectsApi.list()
    projects.value = res.data.projects
    activeProject.value = res.data.active_project ?? ''
  }

  async function loadActive() {
    const res = await projectsApi.active()
    activeProject.value = res.data.active_project ?? ''
    activeProjectData.value = res.data.project ?? null
  }

  async function createProject(name: string, fp = '') {
    await projectsApi.create(name, fp)
    await loadProjects()
    await activateProject(name)
  }

  async function activateProject(name: string) {
    const res = await projectsApi.activate(name)
    activeProject.value = name
    activeProjectData.value = res.data.project ?? null
    await loadProjects()
  }

  async function saveProject(data: Partial<Project>) {
    if (!activeProject.value) return
    await projectsApi.update(activeProject.value, data as Record<string, unknown>)
    await loadActive()
  }

  async function discoverProjects() {
    const res = await projectsApi.discover()
    await loadProjects()
    return res.data as { discovered: string[]; message: string }
  }

  async function deleteProject(name: string) {
    const wasActive = activeProject.value === name
    await projectsApi.delete(name)
    if (wasActive) {
      activeProject.value = ''
      activeProjectData.value = null
    }
    await loadProjects()
  }

  return {
    projects,
    activeProject,
    activeProjectData,
    loading,
    filepath,
    loadProjects,
    loadActive,
    createProject,
    activateProject,
    saveProject,
    discoverProjects,
    deleteProject,
  }
})
