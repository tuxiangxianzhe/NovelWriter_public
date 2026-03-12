import { defineStore } from 'pinia'
import { ref } from 'vue'
import { generateApi } from '@/api/client'
import { useProjectStore } from './project'

export const useGenerateStore = defineStore('generate', () => {
  const architectureContent = ref('')
  const blueprintContent = ref('')
  const characterDynamicsContent = ref('')
  const architectureExists = ref(false)
  const blueprintExists = ref(false)
  const characterDynamicsExists = ref(false)

  // 各独立文件内容
  const coreSeedContent = ref('')
  const worldBuildingContent = ref('')
  const plotArchitectureContent = ref('')
  const characterStateContent = ref('')

  async function loadStatus() {
    const projectStore = useProjectStore()
    const res = await generateApi.status(projectStore.filepath)
    architectureExists.value = res.data.architecture_exists
    blueprintExists.value = res.data.blueprint_exists
    architectureContent.value = res.data.architecture_content ?? ''
    blueprintContent.value = res.data.blueprint_content ?? ''
    characterDynamicsExists.value = res.data.character_dynamics_exists ?? false
    characterDynamicsContent.value = res.data.character_dynamics_content ?? ''
    coreSeedContent.value = res.data.core_seed_content ?? ''
    worldBuildingContent.value = res.data.world_building_content ?? ''
    plotArchitectureContent.value = res.data.plot_architecture_content ?? ''
    characterStateContent.value = res.data.character_state_content ?? ''
  }

  return {
    architectureContent,
    blueprintContent,
    characterDynamicsContent,
    architectureExists,
    blueprintExists,
    characterDynamicsExists,
    coreSeedContent,
    worldBuildingContent,
    plotArchitectureContent,
    characterStateContent,
    loadStatus,
  }
})
