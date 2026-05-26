<template>
  <div class="px-4 py-4">
    <div class="flex items-center justify-between mb-4">
      <h2 class="font-serif font-bold text-sage-800">{{ isEdit ? '编辑日记' : '新增日记' }}</h2>
      <button v-if="!isEdit" type="button" @click="showAiEntry = true"
        class="px-3 py-1.5 text-xs bg-gold-400 text-white rounded-lg hover:bg-gold-500 transition-colors">
        AI 录入
      </button>
    </div>

    <!-- AI Entry Modal -->
    <div v-if="showAiEntry" class="fixed inset-0 bg-ink-900/40 z-50 flex items-end sm:items-center justify-center p-4">
      <div class="bg-white rounded-t-2xl sm:rounded-2xl w-full max-w-md p-5 space-y-3">
        <h3 class="font-serif font-bold text-sage-800">AI 自动录入</h3>
        <textarea v-model="aiText" rows="4" placeholder="描述今天的修行...或者点击录音按钮"
          class="w-full px-4 py-3 rounded-lg border border-sage-200 text-sm focus:outline-none focus:border-sage-500 resize-none"></textarea>
        <button @click="startVoice" type="button" :disabled="voiceActive"
          class="w-full py-2 border border-sage-300 rounded-lg text-sm text-sage-600 hover:bg-sage-50 disabled:opacity-50 transition-colors">
          {{ voiceActive ? '录音中...点击停止' : '🎤 语音输入' }}
        </button>
        <div class="flex gap-2">
          <button @click="aiEntry" type="button" :disabled="!aiText.trim() || aiLoading"
            class="flex-1 py-2 bg-sage-800 text-white rounded-lg text-sm hover:bg-sage-700 disabled:opacity-50 transition-colors">
            {{ aiLoading ? 'AI 分析中...' : 'AI 录入' }}
          </button>
          <button @click="showAiEntry = false; aiText = ''" type="button"
            class="flex-1 py-2 border border-sage-200 rounded-lg text-sm text-sage-500">
            取消
          </button>
        </div>
        <p v-if="aiResultMsg" class="text-xs text-sage-500 text-center">{{ aiResultMsg }}</p>
      </div>
    </div>

    <form @submit.prevent="handleSubmit" class="space-y-4">
      <div>
        <input v-model="form.title" type="text" placeholder="标题（可选）"
          class="w-full px-4 py-3 rounded-lg border border-sage-200 focus:outline-none focus:border-sage-500" />
      </div>

      <div>
        <textarea v-model="form.body" rows="8" placeholder="今天修行了什么？有什么感悟？" required
          class="w-full px-4 py-3 rounded-lg border border-sage-200 focus:outline-none focus:border-sage-500 resize-none"></textarea>
      </div>

      <!-- Mood selector -->
      <div>
        <p class="text-sm text-sage-500 mb-2">心情</p>
        <div class="flex gap-2 flex-wrap">
          <button v-for="m in moods" :key="m.value" type="button"
            @click="form.mood = form.mood === m.value ? null : m.value"
            class="px-3 py-1.5 rounded-full text-sm border transition-colors"
            :class="form.mood === m.value ? 'bg-sage-200 border-sage-400 text-sage-800' : 'bg-white border-sage-200 text-sage-600'">
            {{ m.label }}
          </button>
        </div>
      </div>

      <!-- Category selector -->
      <div>
        <p class="text-sm text-sage-500 mb-2">分类</p>
        <div class="flex gap-2 flex-wrap">
          <button v-for="c in categories" :key="c.value" type="button"
            @click="form.category = form.category === c.value ? null : c.value"
            class="px-3 py-1.5 rounded-full text-sm border transition-colors"
            :class="form.category === c.value ? 'bg-sage-200 border-sage-400 text-sage-800' : 'bg-white border-sage-200 text-sage-600'">
            {{ c.label }}
          </button>
        </div>
      </div>

      <div>
        <label class="text-sm text-sage-500 mb-1 block">修行时长（分钟）</label>
        <input v-model.number="form.duration_minutes" type="number" min="0" max="600" placeholder="0"
          class="w-28 px-4 py-2 rounded-lg border border-sage-200 focus:outline-none focus:border-sage-500" />
      </div>

      <div>
        <label class="text-sm text-sage-500 mb-1 block">日期</label>
        <input v-model="form.practice_date" type="date"
          class="w-full px-4 py-2 rounded-lg border border-sage-200 focus:outline-none focus:border-sage-500" />
      </div>

      <!-- Link content -->
      <div>
        <p class="text-sm text-sage-500 mb-2">关联书库内容（可选）</p>
        <div v-if="contentsLoading" class="text-xs text-sage-400">加载中...</div>
        <div v-else class="space-y-1 max-h-40 overflow-y-auto">
          <label v-for="c in contents" :key="c.id"
            class="flex items-center gap-2 px-3 py-1.5 rounded hover:bg-sage-50 cursor-pointer">
            <input type="checkbox" :value="c.id" v-model="form.content_ids" class="rounded" />
            <span class="text-sm text-sage-700 truncate">{{ c.title }}</span>
            <span class="text-xs text-sage-400">{{ c.source }}</span>
          </label>
        </div>
        <p v-if="!contentsLoading && contents.length === 0" class="text-xs text-sage-400">书库中还没有内容</p>
      </div>

      <p v-if="error" class="text-vermilion-500 text-sm">{{ error }}</p>

      <button type="submit" :disabled="saving"
        class="w-full py-3 bg-sage-800 text-white rounded-lg hover:bg-sage-700 disabled:opacity-50 font-serif transition-colors">
        {{ saving ? '保存中...' : '保存' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApi } from '../composables/useApi'

const route = useRoute()
const router = useRouter()
const api = useApi()
const isEdit = !!route.params.id

const moods = [
  { value: 'calm', label: '平静' },
  { value: 'energized', label: '精力充沛' },
  { value: 'scattered', label: '散乱' },
  { value: 'peaceful', label: '安宁' },
  { value: 'tired', label: '疲惫' },
]

const categories = [
  { value: 'meditation', label: '静坐冥想' },
  { value: 'chanting', label: '诵经持咒' },
  { value: 'reading', label: '阅读经典' },
  { value: 'walking', label: '行禅散步' },
  { value: 'yoga', label: '瑜伽/太极' },
  { value: 'other', label: '其他' },
]

const form = ref({
  title: '',
  body: '',
  mood: null,
  category: null,
  duration_minutes: null,
  practice_date: new Date().toISOString().slice(0, 10),
  content_ids: [],
})

// AI auto-entry
const showAiEntry = ref(false)
const aiText = ref('')
const aiLoading = ref(false)
const aiResultMsg = ref('')
const voiceActive = ref(false)
let recognition = null

const contents = ref([])
const contentsLoading = ref(true)
const saving = ref(false)
const error = ref('')

onMounted(async () => {
  const [contentRes] = await Promise.all([
    api.get('/contents?limit=100'),
    isEdit ? loadEntry() : Promise.resolve(),
  ])
  if (contentRes.data) contents.value = contentRes.data.items
  contentsLoading.value = false
})

async function loadEntry() {
  const { data } = await api.get(`/practices/${route.params.id}`)
  if (data) {
    form.value = {
      title: data.title || '',
      body: data.body,
      mood: data.mood,
      category: data.category,
      duration_minutes: data.duration_minutes,
      practice_date: data.practice_date,
      content_ids: data.linked_contents.map(c => c.id),
    }
  }
}

async function aiEntry() {
  if (!aiText.value.trim() || aiLoading.value) return
  aiLoading.value = true
  aiResultMsg.value = ''
  const { data, error } = await api.post('/ai/auto-entry', { text: aiText.value })
  if (data) {
    form.value.title = data.title || ''
    form.value.body = data.body || aiText.value
    form.value.mood = data.mood
    form.value.category = data.category
    form.value.duration_minutes = data.duration_minutes
    showAiEntry.value = false
    aiText.value = ''
    aiResultMsg.value = ''
  } else {
    aiResultMsg.value = error || '录入失败'
  }
  aiLoading.value = false
}

function startVoice() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SpeechRecognition) {
    aiResultMsg.value = '浏览器不支持语音识别，请用 Chrome'
    return
  }
  if (voiceActive.value) {
    recognition.stop()
    voiceActive.value = false
    return
  }
  recognition = new SpeechRecognition()
  recognition.lang = 'zh-CN'
  recognition.interimResults = false
  recognition.onresult = (e) => {
    aiText.value = e.results[0][0].transcript
    voiceActive.value = false
  }
  recognition.onerror = () => {
    voiceActive.value = false
    aiResultMsg.value = '语音识别失败'
  }
  recognition.onend = () => { voiceActive.value = false }
  recognition.start()
  voiceActive.value = true
}

async function handleSubmit() {
  error.value = ''
  saving.value = true
  try {
    if (isEdit) {
      await api.put(`/practices/${route.params.id}`, form.value)
    } else {
      await api.post('/practices', form.value)
    }
    router.push('/practice')
  } catch (e) {
    error.value = e.message || '保存失败'
  } finally {
    saving.value = false
  }
}
</script>
