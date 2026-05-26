<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useProjectStore } from '@/stores/project'
import { useConfigStore } from '@/stores/config'
import { projectsApi } from '@/api/client'

const projectStore = useProjectStore()
const configStore = useConfigStore()

const showCreate = ref(false)
const newName = ref('')
const newPath = ref('')
const creating = ref(false)
const deleting = ref(false)
const discovering = ref(false)
const statusMsg = ref('')

// 备份相关
const showBackups = ref(false)
const backups = ref<{ id: string; timestamp: string; note: string; size_mb: number }[]>([])
const backupNote = ref('')
const backupLoading = ref(false)

async function loadBackups() {
  const name = projectStore.activeProject
  if (!name) return
  try {
    const res = await projectsApi.listBackups(name)
    backups.value = res.data.backups
  } catch { backups.value = [] }
}

async function onCreateBackup() {
  const name = projectStore.activeProject
  if (!name) return
  backupLoading.value = true
  try {
    const res = await projectsApi.createBackup(name, backupNote.value.trim())
    statusMsg.value = res.data.message
    backupNote.value = ''
    await loadBackups()
  } catch (e: unknown) { statusMsg.value = (e as Error).message }
  finally { backupLoading.value = false }
  setTimeout(() => (statusMsg.value = ''), 3000)
}

async function onRestoreBackup(backupId: string) {
  const name = projectStore.activeProject
  if (!name) return
  if (!confirm(`确定要还原到备份「${backupId}」吗？当前状态会自动备份后再还原。`)) return
  backupLoading.value = true
  try {
    const res = await projectsApi.restoreBackup(name, backupId)
    statusMsg.value = res.data.message
    await loadBackups()
    // 刷新项目内容
    await projectStore.loadActive()
  } catch (e: unknown) { statusMsg.value = (e as Error).message }
  finally { backupLoading.value = false }
  setTimeout(() => (statusMsg.value = ''), 5000)
}

async function onDeleteBackup(backupId: string) {
  const name = projectStore.activeProject
  if (!name) return
  if (!confirm(`确定要删除备份「${backupId}」吗？`)) return
  try {
    await projectsApi.deleteBackup(name, backupId)
    await loadBackups()
  } catch (e: unknown) { statusMsg.value = (e as Error).message }
}

function toggleBackups() {
  showBackups.value = !showBackups.value
  if (showBackups.value) loadBackups()
}

onMounted(async () => {
  await Promise.all([
    projectStore.loadProjects(),
    projectStore.loadActive(),
    configStore.loadAll(),
  ])
})

async function onSelectProject(name: string) {
  if (!name || name === projectStore.activeProject) return
  try {
    await projectStore.activateProject(name)
    statusMsg.value = `已切换到「${name}」`
    setTimeout(() => (statusMsg.value = ''), 2000)
  } catch (e: unknown) {
    statusMsg.value = (e as Error).message
  }
}

async function onDelete() {
  const name = projectStore.activeProject
  if (!name) return
  if (!confirm(`确定要删除项目「${name}」吗？项目文件将被移至 trash 目录。`)) return
  deleting.value = true
  try {
    await projectStore.deleteProject(name)
    statusMsg.value = `已删除「${name}」`
    setTimeout(() => (statusMsg.value = ''), 2000)
  } catch (e: unknown) {
    statusMsg.value = (e as Error).message
  } finally {
    deleting.value = false
  }
}

async function onDiscover() {
  discovering.value = true
  try {
    const res = await projectStore.discoverProjects()
    statusMsg.value = res.message
    setTimeout(() => (statusMsg.value = ''), 3000)
  } catch (e: unknown) {
    statusMsg.value = (e as Error).message
  } finally {
    discovering.value = false
  }
}

async function onCreate() {
  if (!newName.value.trim()) return
  creating.value = true
  try {
    await projectStore.createProject(newName.value.trim(), newPath.value.trim())
    showCreate.value = false
    newName.value = ''
    newPath.value = ''
  } catch (e: unknown) {
    statusMsg.value = (e as Error).message
  } finally {
    creating.value = false
  }
}
</script>

<template>
  <div class="flex items-center gap-3 flex-wrap">
    <!-- 项目选择 -->
    <div class="flex items-center gap-2">
      <label class="text-[var(--color-gold-light)] text-sm font-medium whitespace-nowrap">当前项目</label>
      <select
        :value="projectStore.activeProject"
        @change="onSelectProject(($event.target as HTMLSelectElement).value)"
        class="bg-[var(--color-spine-light)] text-[var(--color-parchment)] border border-[var(--color-gold-dark)] rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--color-gold)]"
      >
        <option value="" disabled>— 选择项目 —</option>
        <option v-for="p in projectStore.projects" :key="p" :value="p">{{ p }}</option>
      </select>
    </div>

    <!-- 新建项目按钮 -->
    <button
      @click="showCreate = !showCreate"
      class="text-[var(--color-gold-light)] border border-[var(--color-gold-dark)] rounded-md px-3 py-1.5 text-sm hover:bg-[var(--color-spine-light)] transition-colors"
      type="button"
    >
      + 新建项目
    </button>

    <!-- 刷新发现项目 -->
    <button
      @click="onDiscover"
      :disabled="discovering"
      class="text-[var(--color-gold-light)] border border-[var(--color-gold-dark)] rounded-md px-3 py-1.5 text-sm hover:bg-[var(--color-spine-light)] disabled:opacity-50 transition-colors"
      type="button"
      title="扫描 output 目录，自动发现并注册已有项目"
    >
      {{ discovering ? '扫描中...' : '刷新发现' }}
    </button>

    <!-- 备份管理按钮 -->
    <button
      v-if="projectStore.activeProject"
      @click="toggleBackups"
      class="text-[var(--color-gold-light)] border border-[var(--color-gold-dark)] rounded-md px-3 py-1.5 text-sm hover:bg-[var(--color-spine-light)] transition-colors"
      type="button"
    >
      {{ showBackups ? '收起备份' : '备份管理' }}
    </button>

    <!-- 删除项目按钮 -->
    <button
      v-if="projectStore.activeProject"
      @click="onDelete"
      :disabled="deleting"
      class="text-red-400 border border-red-400/40 rounded-md px-3 py-1.5 text-sm hover:bg-red-400/10 disabled:opacity-50 transition-colors"
      type="button"
    >
      {{ deleting ? '删除中...' : '删除项目' }}
    </button>

    <!-- 状态消息 -->
    <Transition name="fade">
      <span v-if="statusMsg" class="text-[var(--color-gold-light)] text-xs">{{ statusMsg }}</span>
    </Transition>

    <!-- 新建项目表单（内联弹出） -->
    <Transition name="slide">
      <div v-if="showCreate" class="w-full flex items-center gap-2 flex-wrap mt-1">
        <input
          v-model="newName"
          placeholder="项目名称"
          class="bg-[var(--color-spine-light)] text-[var(--color-parchment)] border border-[var(--color-gold-dark)] rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--color-gold)] w-40"
        />
        <input
          v-model="newPath"
          placeholder="输出路径（可选）"
          class="bg-[var(--color-spine-light)] text-[var(--color-parchment)] border border-[var(--color-gold-dark)] rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--color-gold)] w-52"
        />
        <button
          @click="onCreate"
          :disabled="creating"
          class="bg-[var(--color-gold-dark)] text-[var(--color-ink)] rounded-md px-4 py-1.5 text-sm font-semibold hover:bg-[var(--color-gold)] disabled:opacity-50 transition-colors"
          type="button"
        >
          {{ creating ? '创建中...' : '创建' }}
        </button>
        <button
          @click="showCreate = false"
          class="text-[var(--color-parchment-dark)] text-sm hover:text-[var(--color-parchment)] transition-colors"
          type="button"
        >
          取消
        </button>
      </div>
    </Transition>

    <!-- 备份管理面板 -->
    <Transition name="slide">
      <div v-if="showBackups && projectStore.activeProject" class="w-full mt-1 rounded-md border border-[var(--color-gold-dark)] bg-[var(--color-spine-light)] p-3 space-y-2">
        <!-- 创建备份 -->
        <div class="flex items-center gap-2">
          <input
            v-model="backupNote"
            placeholder="备份备注（可选，如：第5章完成后）"
            class="flex-1 bg-[var(--color-spine)] text-[var(--color-parchment)] border border-[var(--color-gold-dark)] rounded px-2 py-1 text-sm"
          />
          <button
            @click="onCreateBackup"
            :disabled="backupLoading"
            class="bg-[var(--color-gold-dark)] text-[var(--color-ink)] rounded px-3 py-1 text-sm font-semibold hover:bg-[var(--color-gold)] disabled:opacity-50 whitespace-nowrap"
            type="button"
          >
            {{ backupLoading ? '处理中…' : '+ 创建备份' }}
          </button>
        </div>

        <!-- 备份列表 -->
        <div v-if="backups.length === 0" class="text-xs text-[var(--color-parchment-dark)] italic">暂无备份</div>
        <div v-else class="max-h-48 overflow-y-auto space-y-1">
          <div
            v-for="b in backups"
            :key="b.id"
            class="flex items-center gap-2 text-xs text-[var(--color-parchment)] bg-[var(--color-spine)] rounded px-2 py-1.5"
          >
            <span class="flex-1 truncate" :title="b.id">
              {{ b.timestamp }}
              <span v-if="b.note" class="text-[var(--color-gold-light)]"> — {{ b.note }}</span>
              <span class="text-[var(--color-parchment-dark)]"> ({{ b.size_mb }}MB)</span>
            </span>
            <button
              @click="onRestoreBackup(b.id)"
              :disabled="backupLoading"
              class="text-[var(--color-gold-light)] hover:text-[var(--color-gold)] disabled:opacity-50 whitespace-nowrap"
              type="button"
            >还原</button>
            <button
              @click="onDeleteBackup(b.id)"
              class="text-red-400 hover:text-red-300 whitespace-nowrap"
              type="button"
            >删除</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>
