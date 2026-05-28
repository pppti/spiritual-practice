<template>
  <div class="px-4 py-4">
    <div class="text-center mb-6">
      <h2 class="font-serif font-bold text-sage-800 text-xl mb-1">白噪音</h2>
      <p class="text-sm text-sage-500">以自然之声，洗涤尘心</p>
    </div>

    <!-- Upload -->
    <div class="mb-4">
      <label class="flex items-center justify-center gap-2 w-full py-3 border-2 border-dashed border-sage-300 rounded-xl text-sm text-sage-500 hover:border-sage-400 hover:text-sage-600 cursor-pointer transition-colors">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
        </svg>
        导入音频
        <input type="file" accept="audio/*" @change="handleUpload" class="hidden" />
      </label>
      <p v-if="uploadMsg" class="text-xs text-center mt-1" :class="uploadMsg.includes('成功') ? 'text-sage-600' : 'text-vermilion-500'">{{ uploadMsg }}</p>
    </div>

    <div v-if="loading" class="text-center text-sage-400 py-6">加载中...</div>
    <EmptyState v-else-if="trackList.length === 0" text="没有可用的音轨" />

    <!-- Track list -->
    <div v-else class="space-y-3">
      <div v-for="track in trackList" :key="track.id"
        class="bg-white rounded-xl p-4 border border-sage-100 transition-colors"
        :class="{ 'border-sage-400 shadow-sm': activeTracks[track.id]?.playing }">
        <div class="flex items-center justify-between">
          <div>
            <p class="font-medium text-sage-800">{{ track.name_cn || track.name }}</p>
            <p class="text-xs text-sage-400">{{ categoryNames[track.category] || track.category }}</p>
          </div>
          <div class="flex items-center gap-2">
            <button v-if="!track.is_builtin" @click="deleteTrack(track.id)" class="text-xs text-vermilion-500 hover:text-vermilion-600 p-1">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
              </svg>
            </button>
            <!-- Volume -->
            <input v-if="activeTracks[track.id]" type="range" min="0" max="1" step="0.05"
              :value="activeTracks[track.id].volume"
              @input="setVolume(track.id, $event.target.value)"
              class="w-16 h-1 accent-sage-600" />
            <!-- Play/Pause -->
            <button @click="togglePlay(track.id)"
              class="w-10 h-10 rounded-full flex items-center justify-center transition-colors"
              :class="activeTracks[track.id]?.playing ? 'bg-sage-200 text-sage-700' : 'bg-sage-800 text-white'">
              <svg v-if="activeTracks[track.id]?.playing" class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <rect x="6" y="4" width="4" height="16" rx="1"/>
                <rect x="14" y="4" width="4" height="16" rx="1"/>
              </svg>
              <svg v-else class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <polygon points="5,3 19,12 5,21"/>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Stop all -->
      <button v-if="anyPlaying" @click="stopAll"
        class="w-full mt-4 py-3 border border-sage-400 text-sage-700 rounded-lg text-sm hover:bg-sage-100 transition-colors">
        停止全部
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useApi } from '../composables/useApi'
import { useAudio } from '../composables/useAudio'
import EmptyState from '../components/common/EmptyState.vue'

const api = useApi()
const audio = useAudio()
const trackList = ref([])
const loading = ref(true)
const uploadMsg = ref('')
const uploading = ref(false)

const categoryNames = { rain: '雨', water: '水', bell: '钟', bowl: '钵', wind: '风', thunder: '雷' }

const activeTracks = computed(() => {
  const map = {}
  audio.tracks.value.forEach(t => {
    map[t.id] = { playing: t.playing, volume: t.volume }
  })
  return map
})

const anyPlaying = computed(() => audio.tracks.value.some(t => t.playing))

function togglePlay(id) {
  if (!activeTracks.value[id]) {
    const trackData = trackList.value.find(t => t.id === id)
    if (trackData) audio.addTrack(trackData)
  }
  audio.togglePlay(id)
}

function setVolume(trackId, vol) {
  audio.setVolume(trackId, parseFloat(vol))
}

function stopAll() {
  audio.stopAll()
}

async function handleUpload(e) {
  const file = e.target.files[0]
  if (!file || uploading.value) return
  if (file.size > 30 * 1024 * 1024) {
    uploadMsg.value = '文件太大（最大30MB）'
    return
  }
  uploading.value = true
  uploadMsg.value = '上传中...'
  const formData = new FormData()
  formData.append('file', file)
  formData.append('name_cn', file.name.replace(/\.[^/.]+$/, ''))

  const auth = useAuthStore()
  const res = await fetch('/api/white-noise/upload', {
    method: 'POST',
    headers: { Authorization: `Bearer ${auth.token}` },
    body: formData,
  })

  if (res.ok) {
    const track = await res.json()
    trackList.value.push(track)
    uploadMsg.value = '导入成功'
  } else {
    const err = await res.text()
    uploadMsg.value = '导入失败: ' + (res.status === 401 ? '请先登录' : res.status + ' ' + (err || '').slice(0, 50))
  }
  uploading.value = false
  e.target.value = ''
  setTimeout(() => { uploadMsg.value = '' }, 5000)
}

async function deleteTrack(id) {
  if (!confirm('确定删除这个音频？')) return
  const { error } = await api.delete(`/white-noise/tracks/${id}`)
  if (!error) {
    audio.removeTrack(id)
    trackList.value = trackList.value.filter(t => t.id !== id)
  }
}

import { useAuthStore } from '../stores/auth'

onMounted(async () => {
  const { data } = await api.get('/white-noise/tracks')
  if (data) trackList.value = data
  loading.value = false
})
</script>
