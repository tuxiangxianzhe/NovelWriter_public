<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { configApi } from '@/api/client'

const userProfile = ref('')
const profileEnabled = ref(true)
const profileSaving = ref(false)
const profileMsg = ref('')

async function loadProfile() {
  try {
    const res = await configApi.getUserProfile()
    userProfile.value = res.data.profile || ''
    profileEnabled.value = res.data.enabled !== false
  } catch { /* ignore */ }
}

async function saveProfile() {
  profileSaving.value = true
  try {
    await configApi.saveUserProfile(userProfile.value, profileEnabled.value)
    profileMsg.value = '✅ 画像已保存'
  } catch (e: unknown) {
    profileMsg.value = `❌ ${(e as Error).message}`
  }
  profileSaving.value = false
  setTimeout(() => { profileMsg.value = '' }, 3000)
}

onMounted(() => loadProfile())
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-6 space-y-6">
    <h2 class="text-2xl font-bold" style="color: var(--color-ink)">👤 用户画像</h2>

    <div class="rounded-xl border border-[var(--color-parchment-darker)] bg-white overflow-hidden">
      <div class="px-4 py-3 bg-[var(--color-parchment)] border-b border-[var(--color-parchment-darker)] flex items-center justify-between">
        <div>
          <h3 class="text-base font-semibold" style="color: var(--color-leather)">内容偏好</h3>
          <p class="text-xs text-[var(--color-ink-light)] mt-1">记录你的内容偏好（角色类型、XP倾向、关系模式等）。生成架构/角色/剧情/蓝图/细纲时自动参考。全局生效，所有项目共用。</p>
        </div>
        <label class="inline-flex items-center gap-2 cursor-pointer shrink-0 ml-4">
          <input type="checkbox" v-model="profileEnabled" class="rounded border-[var(--color-parchment-darker)]" />
          <span class="text-sm" :class="profileEnabled ? 'text-green-700 font-medium' : 'text-[var(--color-ink-light)]'">{{ profileEnabled ? '已启用' : '已禁用' }}</span>
        </label>
      </div>
      <div class="p-4 space-y-3">
        <textarea
          v-model="userProfile"
          rows="12"
          class="w-full border border-[var(--color-parchment-darker)] rounded-md px-3 py-2 text-sm font-mono resize-y"
          placeholder="例如：
- 女角色偏好自愿而非强迫
- 喜欢年上姐姐型角色，温柔包容
- 催眠后角色保留意识但无法抗拒
- 偏好角色之间先有情感基础再发展肉体关系
- 不喜欢纯粹的暴力强制
- 官能场景偏好支配/服从的权力差但基于信任"
        />
        <div class="flex items-center justify-between">
          <span v-if="profileMsg" class="text-xs" :class="profileMsg.startsWith('✅') ? 'text-green-600' : 'text-red-500'">{{ profileMsg }}</span>
          <span v-else class="text-xs text-[var(--color-ink-light)]">修改后点击保存，将在下次生成架构/角色/剧情/蓝图/细纲时生效</span>
          <button @click="saveProfile" :disabled="profileSaving"
            class="px-4 py-2 rounded-md text-sm font-semibold text-white disabled:opacity-40 transition-colors"
            style="background-color: var(--color-leather)"
            type="button">
            {{ profileSaving ? '保存中...' : '保存画像' }}
          </button>
        </div>
      </div>
    </div>

    <div class="rounded-xl border border-[var(--color-parchment-darker)] bg-white overflow-hidden">
      <div class="px-4 py-3 bg-[var(--color-parchment)] border-b border-[var(--color-parchment-darker)]">
        <h3 class="text-base font-semibold" style="color: var(--color-leather)">自动采集</h3>
        <p class="text-xs text-[var(--color-ink-light)] mt-1">在创意讨论、修订建议、润色建议中表达偏好时，系统会自动检测并提示你是否加入画像。</p>
      </div>
      <div class="p-4">
        <div class="text-sm text-[var(--color-ink-light)] space-y-2">
          <p>采集来源：</p>
          <ul class="list-disc list-inside space-y-1 text-xs">
            <li><strong>创意讨论</strong> — 发送消息时自动提取偏好信号</li>
            <li><strong>修订建议</strong> — 提交架构/角色/剧情修订时自动提取</li>
            <li><strong>润色建议</strong> — 提交润色请求时自动提取</li>
          </ul>
          <p class="text-xs">检测到偏好后会弹出确认条，点击"加入画像"才会写入，不会自动添加。</p>
        </div>
      </div>
    </div>
  </div>
</template>
