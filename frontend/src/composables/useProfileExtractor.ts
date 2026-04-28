import { ref } from 'vue'
import { configApi } from '@/api/client'

/**
 * 偏好提取 composable
 * 从用户文本中异步提取偏好信号，展示确认条，用户确认后追加到画像
 */
export function useProfileExtractor() {
  const extractedPrefs = ref('')
  const showConfirm = ref(false)
  const extracting = ref(false)
  const confirmMsg = ref('')

  /**
   * 异步提取偏好（不阻塞主流程）
   * @param text 用户输入的文本（修订建议/润色建议/讨论消息）
   * @param llmConfigName 当前LLM配置名
   */
  async function tryExtract(text: string, llmConfigName: string) {
    if (!text || !llmConfigName || text.length < 10) return
    extracting.value = true
    try {
      const res = await configApi.extractPreferences(text, llmConfigName)
      const prefs = res.data.preferences || ''
      if (prefs) {
        extractedPrefs.value = prefs
        showConfirm.value = true
      }
    } catch {
      // 提取失败静默忽略，不影响主流程
    } finally {
      extracting.value = false
    }
  }

  async function confirmAppend() {
    if (!extractedPrefs.value) return
    try {
      await configApi.appendProfile(extractedPrefs.value)
      confirmMsg.value = '✅ 已加入画像'
    } catch {
      confirmMsg.value = '❌ 保存失败'
    }
    showConfirm.value = false
    extractedPrefs.value = ''
    setTimeout(() => { confirmMsg.value = '' }, 3000)
  }

  function dismissExtract() {
    showConfirm.value = false
    extractedPrefs.value = ''
  }

  return {
    extractedPrefs,
    showConfirm,
    extracting,
    confirmMsg,
    tryExtract,
    confirmAppend,
    dismissExtract,
  }
}
