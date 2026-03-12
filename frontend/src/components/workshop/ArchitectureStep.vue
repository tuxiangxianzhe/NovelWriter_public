<script setup lang="ts">
import type { useWorkshopState } from '@/composables/useWorkshopState'
import StepCard from '@/components/StepCard.vue'
import StreamOutput from '@/components/StreamOutput.vue'

defineProps<{ state: ReturnType<typeof useWorkshopState> }>()
</script>

<template>
  <StepCard :step="1" title="生成小说架构" description="核心世界观、人物关系、情节走向">
    <div class="space-y-3">
      <!-- 顶部控制栏 -->
      <div class="flex flex-wrap gap-3 items-center">
        <div>
          <label class="block text-xs text-[var(--color-ink-light)] mb-1">叙事DNA</label>
          <select v-model="state.archStyle.value" class="border border-[var(--color-parchment-darker)] rounded-md px-3 py-1.5 text-sm">
            <option v-for="s in state.styleList.value" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
        <div>
          <label class="block text-xs text-[var(--color-ink-light)] mb-1">角色人数</label>
          <input v-model="state.numCharacters.value" placeholder="3-6" class="w-20 border border-[var(--color-parchment-darker)] rounded-md px-3 py-1.5 text-sm" />
        </div>
        <div class="flex-1" />
        <label class="flex items-center gap-2 text-sm cursor-pointer select-none">
          <input type="checkbox" v-model="state.stepMode.value" class="accent-[var(--color-leather)]" />
          分步生成模式
        </label>
        <button
          v-if="!state.stepMode.value"
          @click="state.doGenerateArch()"
          :disabled="state.arch.value.running || !state.llmConfig.value"
          class="btn-primary"
          type="button"
        >
          {{ state.arch.value.running ? '生成中…' : '▶ 生成架构' }}
        </button>
      </div>

      <!-- 分步生成按钮区（仅 stepMode） -->
      <div v-if="state.stepMode.value" class="text-xs text-[var(--color-ink-light)] bg-[var(--color-parchment)] rounded-lg p-3 border border-[var(--color-parchment-darker)]">
        分步生成：按顺序生成各部分，每步可修改后再继续下一步，最后组装为完整架构。
      </div>

      <!-- 始终可见的 5 个组件编辑器 -->

      <!-- ① 核心种子 -->
      <div class="border border-[var(--color-parchment-darker)] rounded-lg p-3 bg-white">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-semibold text-[var(--color-leather)]">① 核心种子</span>
          <div class="flex items-center gap-2">
            <span v-if="state.stepSeed.value.running" class="text-xs text-[var(--color-ink-light)] italic">{{ state.stepSeed.value.progress || '生成中…' }}</span>
            <button v-if="state.stepMode.value" @click="state.doStepSeed()" :disabled="state.stepSeed.value.running || !state.llmConfig.value" class="btn-sm" type="button">
              {{ state.stepSeed.value.running ? '生成中…' : '▶ 生成种子' }}
            </button>
            <button @click="state.saveCoreSeed()" :disabled="!state.seedText.value" class="btn-sm" type="button">💾 保存</button>
          </div>
        </div>
        <textarea v-model="state.seedText.value" rows="8" placeholder="点击【生成种子】自动填充，也可手动编写或修改…"
          class="w-full border border-[var(--color-parchment-darker)] rounded px-3 py-2 text-sm font-mono resize-y"
          style="min-height: 180px" />
        <p v-if="state.stepSeed.value.error" class="text-xs text-red-500 mt-1">{{ state.stepSeed.value.error }}</p>
      </div>

      <!-- ② 角色动力学 -->
      <div class="border border-[var(--color-parchment-darker)] rounded-lg p-3 bg-white">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-semibold text-[var(--color-leather)]">② 角色动力学</span>
          <div class="flex items-center gap-2">
            <span v-if="state.stepChar.value.running" class="text-xs text-[var(--color-ink-light)] italic">{{ state.stepChar.value.progress || '生成中…' }}</span>
            <button v-if="state.stepMode.value" @click="state.doStepChar()" :disabled="state.stepChar.value.running || !state.seedText.value || !state.llmConfig.value" class="btn-sm" type="button">
              {{ state.stepChar.value.running ? '生成中…' : '▶ 生成角色' }}
            </button>
            <button @click="state.saveCharDynamics()" :disabled="!state.charText.value" class="btn-sm" type="button">💾 保存</button>
          </div>
        </div>
        <p v-if="state.stepMode.value && !state.seedText.value" class="text-xs text-[var(--color-ink-light)] mb-1 italic">请先完成①核心种子</p>
        <p class="text-xs text-[var(--color-ink-light)] mb-1">角色关系、性格冲突、成长弧线等动态设定。</p>
        <textarea v-model="state.charText.value" rows="8" placeholder="基于核心种子生成角色动力学，可修改…"
          class="w-full border border-[var(--color-parchment-darker)] rounded px-3 py-2 text-sm font-mono resize-y"
          style="min-height: 180px" />
        <p v-if="state.stepChar.value.error" class="text-xs text-red-500 mt-1">{{ state.stepChar.value.error }}</p>

        <!-- 补充角色子面板 -->
        <details v-if="state.charText.value" class="mt-2 border border-dashed border-[var(--color-parchment-darker)] rounded-lg">
          <summary class="px-3 py-2 cursor-pointer text-xs font-medium text-[var(--color-leather)] select-none">
            ＋ 补充角色（基于已有角色追加新角色）
          </summary>
          <div class="px-3 pb-3 pt-1 space-y-2">
            <div class="flex gap-2 items-end flex-wrap">
              <div class="flex-1">
                <label class="block text-xs text-[var(--color-ink-light)] mb-1">补充要求</label>
                <input v-model="state.supplementGuidance.value" placeholder="例如：增加一个反派角色、增加女主的闺蜜…" class="w-full border border-[var(--color-parchment-darker)] rounded px-2 py-1 text-sm" />
              </div>
              <div>
                <label class="block text-xs text-[var(--color-ink-light)] mb-1">补充人数</label>
                <input v-model="state.supplementNum.value" placeholder="1-2" class="w-16 border border-[var(--color-parchment-darker)] rounded px-2 py-1 text-sm text-center" />
              </div>
              <button @click="state.doSupplementChar()" :disabled="state.supplementChar.value.running || !state.charText.value || !state.llmConfig.value" class="btn-sm" type="button">
                {{ state.supplementChar.value.running ? '生成中…' : '▶ 生成补充角色' }}
              </button>
            </div>
            <p v-if="state.supplementChar.value.progress" class="text-xs text-[var(--color-ink-light)]">{{ state.supplementChar.value.progress }}</p>
            <p v-if="state.supplementChar.value.error" class="text-xs text-red-500">{{ state.supplementChar.value.error }}</p>
            <div v-if="state.supplementResult.value">
              <label class="block text-xs text-[var(--color-ink-light)] mb-1">生成结果（可编辑后再追加）</label>
              <textarea v-model="state.supplementResult.value" rows="6" class="w-full border border-[var(--color-parchment-darker)] rounded px-3 py-2 text-sm font-mono resize-y" />
              <div class="flex justify-end gap-2 mt-1">
                <button @click="state.supplementResult.value = ''" class="btn-sm" type="button">清空</button>
                <button @click="state.appendSupplementChar()" class="btn-sm" type="button">✅ 追加到角色列表</button>
              </div>
            </div>
          </div>
        </details>
      </div>

      <!-- ③ 角色状态 -->
      <div class="border border-[var(--color-parchment-darker)] rounded-lg p-3 bg-white">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-semibold text-[var(--color-leather)]">③ 角色状态</span>
          <div class="flex items-center gap-2">
            <span v-if="state.stepCharState.value.running" class="text-xs text-[var(--color-ink-light)] italic">{{ state.stepCharState.value.progress || '生成中…' }}</span>
            <button v-if="state.stepMode.value" @click="state.doStepCharState()" :disabled="state.stepCharState.value.running || !state.charText.value || !state.llmConfig.value" class="btn-sm" type="button">
              {{ state.stepCharState.value.running ? '生成中…' : '▶ 生成状态' }}
            </button>
            <button @click="state.saveCharState()" :disabled="!state.charStateText.value" class="btn-sm" type="button">💾 保存</button>
          </div>
        </div>
        <p v-if="state.stepMode.value && !state.charText.value" class="text-xs text-[var(--color-ink-light)] mb-1 italic">请先完成②角色动力学</p>
        <p class="text-xs text-[var(--color-ink-light)] mb-1">基于角色动力学生成各角色初始属性、状态快照。</p>
        <textarea v-model="state.charStateText.value" rows="8" placeholder="基于角色动力学生成角色状态…"
          class="w-full border border-[var(--color-parchment-darker)] rounded px-3 py-2 text-sm font-mono resize-y"
          style="min-height: 180px" />
        <p v-if="state.stepCharState.value.error" class="text-xs text-red-500 mt-1">{{ state.stepCharState.value.error }}</p>
      </div>

      <!-- ④ 世界观 -->
      <div class="border border-[var(--color-parchment-darker)] rounded-lg p-3 bg-white">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-semibold text-[var(--color-leather)]">④ 世界观</span>
          <div class="flex items-center gap-2">
            <label class="flex items-center gap-1 text-xs cursor-pointer select-none whitespace-nowrap">
              <input type="checkbox" v-model="state.injectCharToWorld.value" class="accent-[var(--color-leather)]" />
              注入角色设定
            </label>
            <span v-if="state.stepWorld.value.running" class="text-xs text-[var(--color-ink-light)] italic">{{ state.stepWorld.value.progress || '生成中…' }}</span>
            <button v-if="state.stepMode.value" @click="state.doStepWorld()" :disabled="state.stepWorld.value.running || !state.seedText.value || !state.llmConfig.value" class="btn-sm" type="button">
              {{ state.stepWorld.value.running ? '生成中…' : '▶ 生成世界观' }}
            </button>
            <button @click="state.saveWorldBuilding()" :disabled="!state.worldText.value" class="btn-sm" type="button">💾 保存</button>
          </div>
        </div>
        <p v-if="state.stepMode.value && !state.seedText.value" class="text-xs text-[var(--color-ink-light)] mb-1 italic">请先完成①核心种子</p>
        <textarea v-model="state.worldText.value" rows="8" placeholder="基于核心种子生成世界观设定…"
          class="w-full border border-[var(--color-parchment-darker)] rounded px-3 py-2 text-sm font-mono resize-y"
          style="min-height: 180px" />
        <p v-if="state.stepWorld.value.error" class="text-xs text-red-500 mt-1">{{ state.stepWorld.value.error }}</p>
      </div>

      <!-- ⑤ 情节架构 -->
      <div class="border border-[var(--color-parchment-darker)] rounded-lg p-3 bg-white">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-semibold text-[var(--color-leather)]">⑤ 情节架构</span>
          <div class="flex items-center gap-2">
            <span v-if="state.stepPlot.value.running" class="text-xs text-[var(--color-ink-light)] italic">{{ state.stepPlot.value.progress || '生成中…' }}</span>
            <button v-if="state.stepMode.value" @click="state.doStepPlot()" :disabled="state.stepPlot.value.running || !state.seedText.value || !state.charText.value || !state.worldText.value || !state.llmConfig.value" class="btn-sm" type="button">
              {{ state.stepPlot.value.running ? '生成中…' : '▶ 生成情节' }}
            </button>
            <button @click="state.savePlotArch()" :disabled="!state.plotText.value" class="btn-sm" type="button">💾 保存</button>
          </div>
        </div>
        <p v-if="state.stepMode.value && (!state.seedText.value || !state.charText.value || !state.worldText.value)" class="text-xs text-[var(--color-ink-light)] mb-1 italic">请先完成①②④步骤</p>
        <textarea v-model="state.plotText.value" rows="8" placeholder="基于种子、角色和世界观生成情节架构…"
          class="w-full border border-[var(--color-parchment-darker)] rounded px-3 py-2 text-sm font-mono resize-y"
          style="min-height: 180px" />
        <p v-if="state.stepPlot.value.error" class="text-xs text-red-500 mt-1">{{ state.stepPlot.value.error }}</p>
      </div>

      <!-- 组装按钮（仅 stepMode） -->
      <div v-if="state.stepMode.value" class="flex justify-end">
        <button @click="state.doAssemble()" :disabled="!state.seedText.value || !state.charText.value || !state.worldText.value || !state.plotText.value" class="btn-primary" type="button">
          ▶ 组装为完整架构
        </button>
      </div>

      <!-- 组装视图（只读） -->
      <details v-if="state.arch.value.result || state.arch.value.running" class="border border-[var(--color-parchment-darker)] rounded-lg">
        <summary class="px-4 py-2 cursor-pointer text-sm font-medium text-[var(--color-leather)] select-none">
          组装视图（只读）
        </summary>
        <div class="px-4 pb-4 pt-2">
          <StreamOutput
            :progress="state.arch.value.progress"
            :result="state.arch.value.result"
            :error="state.arch.value.error"
            :running="state.arch.value.running"
            :editable="false"
            :progress-value="state.arch.value.progressValue"
            :cancelable="true"
            placeholder="架构内容将在此显示…"
            @cancel="state.cancelSSE(state.arch.value)"
          />
        </div>
      </details>

      <!-- 续写区 -->
      <details class="border border-[var(--color-parchment-darker)] rounded-lg">
        <summary class="px-4 py-2 cursor-pointer text-sm font-medium text-[var(--color-leather)] select-none">
          续写章节弧（扩展新章节）
        </summary>
        <div class="px-4 pb-4 pt-2 space-y-2">
          <div class="flex gap-3 flex-wrap">
            <div>
              <label class="block text-xs text-[var(--color-ink-light)] mb-1">续写章节数</label>
              <input v-model.number="state.newChapters.value" type="number" min="1" class="w-24 border border-[var(--color-parchment-darker)] rounded px-2 py-1 text-sm" />
            </div>
            <div>
              <label class="block text-xs text-[var(--color-ink-light)] mb-1">新增角色人数</label>
              <input v-model="state.contNumCharacters.value" placeholder="1-3" class="w-24 border border-[var(--color-parchment-darker)] rounded px-2 py-1 text-sm" />
            </div>
            <div class="flex-1">
              <label class="block text-xs text-[var(--color-ink-light)] mb-1">续写指导</label>
              <input v-model="state.continueGuidance.value" placeholder="可选" class="w-full border border-[var(--color-parchment-darker)] rounded px-2 py-1 text-sm" />
            </div>
            <div class="flex items-end">
              <button @click="state.doContinueArch()" :disabled="state.continueArch.value.running" class="btn-primary" type="button">
                {{ state.continueArch.value.running ? '生成中…' : '▶ 续写' }}
              </button>
            </div>
          </div>
          <!-- 压缩上下文 -->
          <div class="flex gap-3 items-center">
            <button @click="state.doCompressContext()" :disabled="state.compressRunning.value"
              class="px-3 py-1.5 rounded-md text-sm font-medium border border-[var(--color-parchment-darker)] bg-[var(--color-parchment)] text-[var(--color-leather)] hover:bg-[var(--color-parchment-dark)] disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap transition-colors"
              type="button">
              {{ state.compressRunning.value ? '压缩中…' : '压缩上下文' }}
            </button>
            <label class="flex items-center gap-1.5 text-sm cursor-pointer select-none whitespace-nowrap">
              <input type="checkbox" v-model="state.compressWorldBuilding.value" class="accent-[var(--color-leather)]" />
              同时压缩世界观
            </label>
            <span v-if="state.compressResult.value" class="text-xs whitespace-pre-line" :class="state.compressResult.value.startsWith('❌') ? 'text-red-600' : 'text-green-700'">
              {{ state.compressResult.value }}
            </span>
          </div>

          <div class="flex gap-3 flex-wrap items-end">
            <div>
              <label class="block text-xs text-[var(--color-ink-light)] mb-1">续写叙事DNA</label>
              <select v-model="state.contStyle.value" class="border border-[var(--color-parchment-darker)] rounded-md px-3 py-1.5 text-sm">
                <option v-for="s in state.styleList.value" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
            <div class="flex-1">
              <label class="block text-xs text-[var(--color-ink-light)] mb-1">续写XP类型（可选）</label>
              <input v-model="state.contXpType.value" placeholder="可留空，或输入新的XP方向" class="w-full border border-[var(--color-parchment-darker)] rounded px-2 py-1 text-sm" />
            </div>
          </div>
          <StreamOutput
            :progress="state.continueArch.value.progress"
            :result="state.continueArch.value.result"
            :error="state.continueArch.value.error"
            :running="state.continueArch.value.running"
            :progress-value="state.continueArch.value.progressValue"
            :cancelable="true"
            @cancel="state.cancelSSE(state.continueArch.value)"
          />

          <!-- 分步续写 -->
          <div class="pt-2 border-t border-[var(--color-parchment-darker)]">
            <label class="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" v-model="state.contStepMode.value" class="rounded" />
              分步续写模式（逐步介入编辑）
            </label>
          </div>

          <div v-show="state.contStepMode.value" class="space-y-3 pt-2">
            <!-- C⓪ 续写方向大纲 -->
            <div class="border border-[var(--color-parchment-darker)] rounded-lg p-3 space-y-2">
              <h4 class="text-sm font-medium text-[var(--color-leather)]">C⓪ 续写方向大纲</h4>
              <button @click="state.doContStepSeed()" :disabled="state.contStepSeed.value.running" class="btn-primary" type="button">
                {{ state.contStepSeed.value.running ? '生成中…' : '▶ 生成续写方向大纲' }}
              </button>
              <p v-if="state.contStepSeed.value.error" class="text-xs text-red-600">{{ state.contStepSeed.value.error }}</p>
              <p v-if="state.contStepSeed.value.progress" class="text-xs text-[var(--color-ink-light)]">{{ state.contStepSeed.value.progress }}</p>
              <textarea v-model="state.contSeedText.value" rows="8" class="w-full border border-[var(--color-parchment-darker)] rounded p-2 text-sm" placeholder="续写方向大纲将在此显示，可手动编辑…"></textarea>
            </div>

            <!-- C⓪.5 世界观扩展 -->
            <div class="border border-[var(--color-parchment-darker)] rounded-lg p-3 space-y-2">
              <h4 class="text-sm font-medium text-[var(--color-leather)]">C⓪.5 世界观扩展</h4>
              <button @click="state.doContStepWorld()" :disabled="state.contStepWorld.value.running" class="btn-primary" type="button">
                {{ state.contStepWorld.value.running ? '生成中…' : '▶ 生成世界观扩展' }}
              </button>
              <p v-if="state.contStepWorld.value.error" class="text-xs text-red-600">{{ state.contStepWorld.value.error }}</p>
              <p v-if="state.contStepWorld.value.progress" class="text-xs text-[var(--color-ink-light)]">{{ state.contStepWorld.value.progress }}</p>
              <textarea v-model="state.contWorldText.value" rows="8" class="w-full border border-[var(--color-parchment-darker)] rounded p-2 text-sm" placeholder="世界观扩展将在此显示，可手动编辑…"></textarea>
            </div>

            <!-- C① 新增角色 -->
            <div class="border border-[var(--color-parchment-darker)] rounded-lg p-3 space-y-2">
              <div class="flex items-center gap-3">
                <h4 class="text-sm font-medium text-[var(--color-leather)]">C① 新增角色</h4>
                <label class="text-xs text-[var(--color-ink-light)] whitespace-nowrap">新增人数</label>
                <input v-model="state.contNumCharacters.value" placeholder="1-3" class="w-16 border border-[var(--color-parchment-darker)] rounded px-2 py-1 text-sm text-center" />
              </div>
              <button @click="state.doContStepChars()" :disabled="state.contStepChars.value.running" class="btn-primary" type="button">
                {{ state.contStepChars.value.running ? '生成中…' : '▶ 生成新增角色' }}
              </button>
              <p v-if="state.contStepChars.value.error" class="text-xs text-red-600">{{ state.contStepChars.value.error }}</p>
              <p v-if="state.contStepChars.value.progress" class="text-xs text-[var(--color-ink-light)]">{{ state.contStepChars.value.progress }}</p>
              <textarea v-model="state.contCharsText.value" rows="8" class="w-full border border-[var(--color-parchment-darker)] rounded p-2 text-sm" placeholder="新增角色设定将在此显示，可手动编辑…"></textarea>

              <!-- 续写补充角色子面板 -->
              <details v-if="state.contCharsText.value" class="border border-dashed border-[var(--color-parchment-darker)] rounded-lg">
                <summary class="px-3 py-2 cursor-pointer text-xs font-medium text-[var(--color-leather)] select-none">
                  ＋ 补充角色（基于已有新增角色追加）
                </summary>
                <div class="px-3 pb-3 pt-1 space-y-2">
                  <div class="flex gap-2 items-end flex-wrap">
                    <div class="flex-1">
                      <label class="block text-xs text-[var(--color-ink-light)] mb-1">补充要求</label>
                      <input v-model="state.contSupplementGuidance.value" placeholder="例如：增加一个新的对手角色…" class="w-full border border-[var(--color-parchment-darker)] rounded px-2 py-1 text-sm" />
                    </div>
                    <div>
                      <label class="block text-xs text-[var(--color-ink-light)] mb-1">补充人数</label>
                      <input v-model="state.contSupplementNum.value" placeholder="1-2" class="w-16 border border-[var(--color-parchment-darker)] rounded px-2 py-1 text-sm text-center" />
                    </div>
                    <button @click="state.doContSupplementChar()" :disabled="state.contSupplementChar.value.running || !state.contCharsText.value || !state.llmConfig.value" class="btn-sm" type="button">
                      {{ state.contSupplementChar.value.running ? '生成中…' : '▶ 生成补充角色' }}
                    </button>
                  </div>
                  <p v-if="state.contSupplementChar.value.progress" class="text-xs text-[var(--color-ink-light)]">{{ state.contSupplementChar.value.progress }}</p>
                  <p v-if="state.contSupplementChar.value.error" class="text-xs text-red-500">{{ state.contSupplementChar.value.error }}</p>
                  <div v-if="state.contSupplementResult.value">
                    <label class="block text-xs text-[var(--color-ink-light)] mb-1">生成结果（可编辑后再追加）</label>
                    <textarea v-model="state.contSupplementResult.value" rows="6" class="w-full border border-[var(--color-parchment-darker)] rounded px-3 py-2 text-sm font-mono resize-y" />
                    <div class="flex justify-end gap-2 mt-1">
                      <button @click="state.contSupplementResult.value = ''" class="btn-sm" type="button">清空</button>
                      <button @click="state.appendContSupplementChar()" class="btn-sm" type="button">✅ 追加到角色列表</button>
                    </div>
                  </div>
                </div>
              </details>
            </div>

            <!-- C② 新增剧情弧 -->
            <div class="border border-[var(--color-parchment-darker)] rounded-lg p-3 space-y-2">
              <h4 class="text-sm font-medium text-[var(--color-leather)]">C② 新增剧情弧</h4>
              <button @click="state.doContStepArcs()" :disabled="state.contStepArcs.value.running || !state.contCharsText.value" class="btn-primary" type="button">
                {{ state.contStepArcs.value.running ? '生成中…' : '▶ 生成新增剧情弧' }}
              </button>
              <p v-if="state.contStepArcs.value.error" class="text-xs text-red-600">{{ state.contStepArcs.value.error }}</p>
              <p v-if="state.contStepArcs.value.progress" class="text-xs text-[var(--color-ink-light)]">{{ state.contStepArcs.value.progress }}</p>
              <textarea v-model="state.contArcsText.value" rows="8" class="w-full border border-[var(--color-parchment-darker)] rounded p-2 text-sm" placeholder="新增剧情弧将在此显示，可手动编辑…"></textarea>
            </div>

            <!-- C③ 新角色状态 -->
            <div class="border border-[var(--color-parchment-darker)] rounded-lg p-3 space-y-2">
              <h4 class="text-sm font-medium text-[var(--color-leather)]">C③ 新角色状态</h4>
              <button @click="state.doContStepCharState()" :disabled="state.contStepCharState.value.running || !state.contCharsText.value" class="btn-primary" type="button">
                {{ state.contStepCharState.value.running ? '生成中…' : '▶ 生成新角色状态' }}
              </button>
              <p v-if="state.contStepCharState.value.error" class="text-xs text-red-600">{{ state.contStepCharState.value.error }}</p>
              <p v-if="state.contStepCharState.value.progress" class="text-xs text-[var(--color-ink-light)]">{{ state.contStepCharState.value.progress }}</p>
              <textarea v-model="state.contCharStateText.value" rows="8" class="w-full border border-[var(--color-parchment-darker)] rounded p-2 text-sm" placeholder="新角色状态将在此显示，可手动编辑…"></textarea>
            </div>

            <!-- 追加按钮 -->
            <div class="flex justify-end">
              <button @click="state.doContAssemble()" :disabled="!state.contCharsText.value || !state.contArcsText.value" class="btn-primary" type="button">
                ▶ 追加到架构文件
              </button>
            </div>
          </div>
        </div>
      </details>
    </div>
  </StepCard>
</template>
