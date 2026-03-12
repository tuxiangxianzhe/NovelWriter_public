<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useProjectStore } from '@/stores/project'
import { useConfigStore } from '@/stores/config'

const projectStore = useProjectStore()
const configStore = useConfigStore()

const showCreate = ref(false)
const newName = ref('')
const newPath = ref('')
const creating = ref(false)
const deleting = ref(false)
const discovering = ref(false)
const statusMsg = ref('')

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
  </div>
</template>
