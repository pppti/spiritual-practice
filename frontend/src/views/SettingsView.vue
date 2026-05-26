<template>
  <div class="px-4 py-4">
    <h2 class="font-serif font-bold text-sage-800 mb-6">设置</h2>

    <div class="space-y-3">
      <div class="bg-white rounded-xl p-4 border border-sage-200">
        <p class="text-sm text-sage-500">当前用户</p>
        <p class="font-medium text-sage-800">{{ user?.username }}</p>
      </div>

      <router-link to="/messages"
        class="block bg-white rounded-xl p-4 border border-sage-200 hover:border-sage-400 transition-colors">
        <div class="flex items-center justify-between">
          <span class="text-sage-800">修行寄语</span>
          <span class="text-sage-400">&rsaquo;</span>
        </div>
      </router-link>

      <router-link to="/white-noise"
        class="block bg-white rounded-xl p-4 border border-sage-200 hover:border-sage-400 transition-colors">
        <div class="flex items-center justify-between">
          <span class="text-sage-800">白噪音</span>
          <span class="text-sage-400">&rsaquo;</span>
        </div>
      </router-link>

      <button @click="backupToGitHub" :disabled="backupLoading"
        class="w-full bg-white rounded-xl p-4 border border-sage-200 hover:border-sage-400 transition-colors text-left">
        <div class="flex items-center justify-between">
          <span class="text-sage-800">备份到 GitHub</span>
          <span class="text-xs" :class="backupMsg === '已备份' ? 'text-sage-600' : 'text-sage-400'">{{ backupMsg }}</span>
        </div>
      </button>

      <button @click="restoreFromGitHub" :disabled="restoreLoading"
        class="w-full bg-white rounded-xl p-4 border border-sage-200 hover:border-sage-400 transition-colors text-left">
        <div class="flex items-center justify-between">
          <span class="text-sage-800">从 GitHub 恢复</span>
          <span class="text-xs text-sage-400">{{ restoreMsg }}</span>
        </div>
      </button>

      <button @click="exportData"
        class="w-full bg-white rounded-xl p-4 border border-sage-200 hover:border-sage-400 transition-colors text-left">
        <div class="flex items-center justify-between">
          <span class="text-sage-800">导出数据 (JSON)</span>
          <span class="text-sage-400">&darr;</span>
        </div>
      </button>

      <button @click="handleLogout"
        class="w-full mt-8 py-3 border border-vermilion-500 text-vermilion-500 rounded-lg hover:bg-vermilion-50 transition-colors">
        退出登录
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useApi } from '../composables/useApi'

const router = useRouter()
const auth = useAuthStore()
const api = useApi()
const user = ref(null)

const backupLoading = ref(false)
const backupMsg = ref('')
const restoreLoading = ref(false)
const restoreMsg = ref('')

onMounted(async () => {
  user.value = auth.user
})

async function backupToGitHub() {
  backupLoading.value = true
  backupMsg.value = '备份中...'
  const { data } = await api.post('/backup/create')
  backupMsg.value = data?.status === 'ok' ? '已备份' : '需配置GITHUB_PAT'
  backupLoading.value = false
  setTimeout(() => { backupMsg.value = '' }, 3000)
}

async function restoreFromGitHub() {
  if (!confirm('将从 GitHub 恢复数据，当前数据将被覆盖，确定继续？')) return
  restoreLoading.value = true
  restoreMsg.value = '恢复中...'
  const { data, error } = await api.post('/backup/restore')
  if (data) {
    restoreMsg.value = '已恢复'
    location.reload()
  } else {
    restoreMsg.value = error || '失败'
  }
  restoreLoading.value = false
  setTimeout(() => { restoreMsg.value = '' }, 3000)
}

async function exportData() {
  const [practicesRes, contentsRes, lotsRes, messagesRes] = await Promise.all([
    api.get('/practices?limit=10000'),
    api.get('/contents?limit=10000'),
    api.get('/lots/history'),
    api.get('/messages'),
  ])

  const data = {
    exported_at: new Date().toISOString(),
    practices: practicesRes.data?.items || [],
    contents: contentsRes.data?.items || [],
    lot_draws: lotsRes.data?.items || [],
    messages: messagesRes.data?.items || [],
  }

  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `practice-backup-${new Date().toISOString().slice(0, 10)}.json`
  a.click()
  URL.revokeObjectURL(url)
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>
