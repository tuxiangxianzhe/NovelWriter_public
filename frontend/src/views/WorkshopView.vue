<script setup lang="ts">
import { useWorkshopState } from '@/composables/useWorkshopState'
import GlobalParamsCard from '@/components/workshop/GlobalParamsCard.vue'
import ArchitectureStep from '@/components/workshop/ArchitectureStep.vue'
import BlueprintStep from '@/components/workshop/BlueprintStep.vue'
import DetailedOutlineStep from '@/components/workshop/DetailedOutlineStep.vue'
import ChapterStep from '@/components/workshop/ChapterStep.vue'
import BatchGenerate from '@/components/workshop/BatchGenerate.vue'
import FinalizeStep from '@/components/workshop/FinalizeStep.vue'
import ExpandStep from '@/components/workshop/ExpandStep.vue'
import HumanizerStep from '@/components/workshop/HumanizerStep.vue'
import ImprovStep from '@/components/workshop/ImprovStep.vue'
import ProfileExtractBar from '@/components/ProfileExtractBar.vue'
import '@/styles/workshop.css'

const state = useWorkshopState()

async function toggleMode() {
  const cur = state.workflowMode.value
  const next = cur === 'improv' ? 'outlined' : 'improv'
  const msg = next === 'improv'
    ? '切换到「即兴模式」？\n\n· 隐藏：全书蓝图、全书细纲、批量生成\n· 显示：单章蓝图、单章细纲、伏笔池\n\n现有全书蓝图保留但本流程不再使用。'
    : '切换回「大纲模式」？\n\n· 隐藏：单章蓝图、单章细纲、伏笔池\n· 显示：全书蓝图、全书细纲、批量生成\n\n现有单章蓝图/细纲/伏笔池保留但本流程不再使用。'
  if (!confirm(msg)) return
  await state.setWorkflowMode(next)
}
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

    <!-- 工作流模式横幅 -->
    <div
      class="rounded-lg px-4 py-3 flex items-center justify-between border"
      :class="state.workflowMode.value === 'improv'
        ? 'bg-orange-50 border-orange-300 text-orange-900'
        : 'bg-blue-50 border-blue-300 text-blue-900'"
    >
      <div class="flex items-center gap-3">
        <span class="text-lg">{{ state.workflowMode.value === 'improv' ? '✨' : '📋' }}</span>
        <div>
          <div class="font-semibold">
            {{ state.workflowMode.value === 'improv' ? '即兴模式 · 逐章生成' : '大纲模式 · 全书规划' }}
          </div>
          <div class="text-xs opacity-80">
            {{ state.workflowMode.value === 'improv'
              ? '不需要全书蓝图。每章前口述意图 → 单章蓝图（可选细纲）→ 正文。伏笔池维持连续性。'
              : '先生成全书架构与章节蓝图，再逐章生成正文。适合心中已有完整规划的写作。'
            }}
          </div>
        </div>
      </div>
      <button @click="toggleMode" class="btn-primary text-sm whitespace-nowrap" type="button">
        切换到{{ state.workflowMode.value === 'improv' ? '大纲模式' : '即兴模式' }}
      </button>
    </div>

    <Transition name="fade">
      <div v-if="state.saveMsg.value" class="px-4 py-2 rounded-md text-sm"
        :class="state.saveMsg.value.startsWith('✅') ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'">
        {{ state.saveMsg.value }}
      </div>
    </Transition>

    <ProfileExtractBar
      :show="state.profileShowConfirm.value"
      :preferences="state.profileExtracted.value"
      :confirm-msg="state.profileConfirmMsg.value"
      @confirm="state.profileConfirmAppend()"
      @dismiss="state.profileDismiss()"
    />

    <GlobalParamsCard :state="state" />
    <ArchitectureStep :state="state" />

    <!-- 大纲模式专属 -->
    <template v-if="state.workflowMode.value !== 'improv'">
      <BlueprintStep :state="state" />
      <DetailedOutlineStep :state="state" />
      <ChapterStep :state="state" />
      <BatchGenerate :state="state" />
    </template>

    <!-- 即兴模式专属 -->
    <template v-else>
      <ImprovStep :state="state" />
    </template>

    <FinalizeStep :state="state" />
    <ExpandStep :state="state" />
    <HumanizerStep :state="state" />
  </div>
</template>
