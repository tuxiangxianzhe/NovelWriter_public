<script setup lang="ts">
import { useWorkshopState } from '@/composables/useWorkshopState'
import GlobalParamsCard from '@/components/workshop/GlobalParamsCard.vue'
import ArchitectureStep from '@/components/workshop/ArchitectureStep.vue'
import BlueprintStep from '@/components/workshop/BlueprintStep.vue'
import ChapterStep from '@/components/workshop/ChapterStep.vue'
import BatchGenerate from '@/components/workshop/BatchGenerate.vue'
import FinalizeStep from '@/components/workshop/FinalizeStep.vue'
import ExpandStep from '@/components/workshop/ExpandStep.vue'
import HumanizerStep from '@/components/workshop/HumanizerStep.vue'
import '@/styles/workshop.css'

const state = useWorkshopState()
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 py-6 space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold" style="color: var(--color-ink)">✍️ 创作工坊</h2>
      <div class="flex items-center gap-2">
        <button @click="state.reloadProjectContent()" :disabled="state.reloading.value" class="btn-primary" type="button"
          title="重新加载当前项目的架构、蓝图等内容">
          {{ state.reloading.value ? '加载中…' : '🔄 重载项目' }}
        </button>
        <button @click="state.doExportNovel()" :disabled="state.exporting.value" class="btn-primary" type="button">
          {{ state.exporting.value ? '导出中…' : '📥 合并导出小说' }}
        </button>
      </div>
    </div>

    <Transition name="fade">
      <div v-if="state.saveMsg.value" class="px-4 py-2 rounded-md text-sm"
        :class="state.saveMsg.value.startsWith('✅') ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'">
        {{ state.saveMsg.value }}
      </div>
    </Transition>

    <GlobalParamsCard :state="state" />
    <ArchitectureStep :state="state" />
    <BlueprintStep :state="state" />
    <ChapterStep :state="state" />
    <BatchGenerate :state="state" />
    <FinalizeStep :state="state" />
    <ExpandStep :state="state" />
    <HumanizerStep :state="state" />
  </div>
</template>
