<template>
  <div class="px-4 py-4">
    <h2 class="font-serif font-bold text-sage-800 mb-4">智能导入</h2>

    <!-- Mode tabs -->
    <div class="flex gap-2 mb-4">
      <button v-for="tab in tabs" :key="tab.key" @click="mode = tab.key"
        class="flex-1 py-2 text-sm rounded-lg transition-colors"
        :class="mode === tab.key ? 'bg-sage-200 text-sage-800 font-medium' : 'bg-white border border-sage-200 text-sage-500'">
        {{ tab.label }}
      </button>
    </div>

    <!-- Text mode -->
    <div v-if="mode === 'text'" class="space-y-3">
      <textarea v-model="inputText" rows="8" placeholder="在此粘贴或输入文字..."
        class="w-full px-4 py-3 rounded-xl border border-sage-200 focus:outline-none focus:border-sage-500 resize-none text-sm"></textarea>
      <button @click="processText" :disabled="!inputText.trim() || loading"
        class="w-full py-3 bg-sage-800 text-white rounded-xl hover:bg-sage-700 disabled:opacity-40 transition-colors font-serif">
        {{ loading ? 'AI 整理中...' : 'AI 整理' }}
      </button>
    </div>

    <!-- File mode -->
    <div v-if="mode === 'file'" class="space-y-3">
      <label class="flex flex-col items-center justify-center w-full py-12 border-2 border-dashed border-sage-300 rounded-xl cursor-pointer hover:border-sage-400 transition-colors">
        <svg class="w-10 h-10 text-sage-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>
        <p class="text-sm text-sage-500">点击上传文件</p>
        <p class="text-xs text-sage-400 mt-1">支持 TXT / DOCX / PDF / MOBI，最大 20MB</p>
        <input type="file" accept=".txt,.docx,.pdf,.mobi,.md" @change="handleFileUpload" class="hidden" />
      </label>
      <p v-if="fileUploadMsg" class="text-sm text-center" :class="fileUploadMsg.includes('成功')||fileUploadMsg.includes('提取') ? 'text-sage-600' : 'text-vermilion-500'">{{ fileUploadMsg }}</p>
      <div v-if="extractedText" class="space-y-3">
        <div class="text-xs text-sage-500 flex items-center justify-between"><span>文件解析结果（{{ extractedText.length }} 字）</span><button @click="fileProcessText" class="text-sage-600 underline">跳过AI整理，直接保存原文</button></div>
        <textarea v-model="extractedText" rows="8" class="w-full px-4 py-3 rounded-xl border border-sage-200 focus:outline-none focus:border-sage-500 resize-none text-sm"></textarea>
        <button @click="processExtractedText" :disabled="!extractedText.trim() || loading" class="w-full py-3 bg-sage-800 text-white rounded-xl hover:bg-sage-700 disabled:opacity-40 transition-colors font-serif">{{ loading ? 'AI 整理中...' : 'AI 整理' }}</button>
      </div>
    </div>

    <!-- Voice mode -->
    <div v-if="mode === 'voice'" class="space-y-3">
      <div class="bg-white rounded-xl p-6 border border-sage-200 text-center">
        <button @click="toggleRecording"
          class="w-20 h-20 rounded-full mx-auto flex items-center justify-center transition-all"
          :class="recording ? 'bg-vermilion-500 animate-pulse' : 'bg-sage-800 hover:bg-sage-700'">
          <svg class="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path v-if="!recording" d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
            <path v-if="!recording" d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
            <rect v-if="recording" x="6" y="6" width="12" height="12" rx="2"/>
          </svg>
        </button>
        <p class="text-sm text-sage-500 mt-3">
          {{ recording ? '录音中...点击停止' : '点击开始录音' }}
        </p>
        <p v-if="recording" class="text-xs text-sage-400 mt-1">已录制 {{ elapsed }}s</p>
      </div>
      <textarea v-if="inputText" v-model="inputText" rows="5" placeholder="录音识别结果..."
        class="w-full px-4 py-3 rounded-xl border border-sage-200 focus:outline-none focus:border-sage-500 resize-none text-sm"></textarea>
      <div v-if="inputText" class="flex gap-2">
        <button @click="processText" :disabled="loading"
          class="flex-1 py-3 bg-sage-800 text-white rounded-xl hover:bg-sage-700 disabled:opacity-40 transition-colors font-serif text-sm">
          {{ loading ? 'AI 整理中...' : 'AI 整理' }}
        </button>
        <button @click="inputText = ''" class="px-4 py-3 border border-sage-200 rounded-xl text-sm text-sage-500">
          清除
        </button>
      </div>
    </div>

    <!-- Screen record mode -->
    <div v-if="mode === 'screen'" class="space-y-3">
      <div class="bg-white rounded-xl p-6 border border-sage-200 text-center">
        <button @click="toggleScreen"
          class="w-20 h-20 rounded-full mx-auto flex items-center justify-center transition-all"
          :class="screenRecording ? 'bg-vermilion-500 animate-pulse' : 'bg-sage-800 hover:bg-sage-700'">
          <svg class="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path v-if="!screenRecording" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/>
            <rect v-if="screenRecording" x="3" y="3" width="18" height="18" rx="2"/>
          </svg>
        </button>
        <p class="text-sm text-sage-500 mt-3">
          {{ screenRecording ? '录屏中...点击停止' : '点击开始录屏' }}
        </p>
        <p class="text-xs text-sage-400 mt-2">录制屏幕+音频，停止后自动转文字</p>
      </div>
      <textarea v-if="inputText" v-model="inputText" rows="5" placeholder="录屏识别结果..."
        class="w-full px-4 py-3 rounded-xl border border-sage-200 focus:outline-none focus:border-sage-500 resize-none text-sm"></textarea>
      <div v-if="inputText" class="flex gap-2">
        <button @click="processText" :disabled="loading"
          class="flex-1 py-3 bg-sage-800 text-white rounded-xl hover:bg-sage-700 disabled:opacity-40 transition-colors font-serif text-sm">
          {{ loading ? 'AI 整理中...' : 'AI 整理' }}
        </button>
        <button @click="inputText = ''" class="px-4 py-3 border border-sage-200 rounded-xl text-sm text-sage-500">清除</button>
      </div>
    </div>

    <!-- Result -->
    <div v-if="result" class="mt-6 space-y-4">
      <div class="bg-gold-50 rounded-xl p-4 border border-gold-200">
        <div v-if="result.content_type" class="text-xs text-gold-600 mb-2">{{ result.content_type || '智能导入' }}</div>

        <label class="text-xs text-sage-500">标题</label>
        <input v-model="result.title" class="w-full px-3 py-2 rounded-lg border border-sage-200 text-sm mb-3 focus:outline-none focus:border-sage-500" />

        <label class="text-xs text-sage-500">正文</label>
        <textarea v-model="result.body" rows="6" class="w-full px-3 py-2 rounded-lg border border-sage-200 text-sm mb-3 focus:outline-none focus:border-sage-500 resize-none"></textarea>

        <div class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="text-xs text-sage-500">分类</label>
            <select v-model="result.category" class="w-full px-3 py-2 rounded-lg border border-sage-200 text-sm bg-white">
              <option v-for="c in categories" :key="c.value" :value="c.value">{{ c.label }}</option>
            </select>
          </div>
          <div>
            <label class="text-xs text-sage-500">心情</label>
            <select v-model="result.mood" class="w-full px-3 py-2 rounded-lg border border-sage-200 text-sm bg-white">
              <option :value="null">不选</option>
              <option v-for="m in moods" :key="m.value" :value="m.value">{{ m.label }}</option>
            </select>
          </div>
        </div>

        <label v-if="result.suggested_tags?.length" class="text-xs text-sage-500">建议标签</label>
        <div class="flex gap-1 flex-wrap">
          <span v-for="tag in result.suggested_tags" :key="tag" class="text-xs px-2 py-0.5 bg-white rounded-full border border-sage-200 text-sage-600">
            {{ tag }}
          </span>
        </div>
      </div>

      <!-- Save buttons -->
      <div class="flex gap-3">
        <button @click="saveAsPractice" :disabled="saving"
          class="flex-1 py-3 bg-sage-800 text-white rounded-xl hover:bg-sage-700 disabled:opacity-40 transition-colors font-serif">
          {{ saving === 'practice' ? '保存中...' : '保存为日记' }}
        </button>
        <button @click="saveAsContent" :disabled="saving"
          class="flex-1 py-3 border border-sage-400 text-sage-700 rounded-xl hover:bg-sage-100 disabled:opacity-40 transition-colors">
          {{ saving === 'content' ? '保存中...' : '保存到书库' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '../composables/useApi'

const router = useRouter()
const api = useApi()

const tabs = [
  { key: 'file', label: '文件' },
  { key: 'text', label: '文字' },
  { key: 'voice', label: '语音' },
  { key: 'screen', label: '录屏' },
]
const mode = ref('text')
const inputText = ref('')
const loading = ref(false)
const saving = ref(false)
const result = ref(null)
const fileUploadMsg = ref('')
const extractedText = ref('')

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

async function handleFileUpload(e) {
  const file = e.target.files[0]; if (!file) return
  if (file.size > 20 * 1024 * 1024) { fileUploadMsg.value = '文件太大（最大20MB）'; return }
  fileUploadMsg.value = '正在解析文件...'
  const formData = new FormData(); formData.append('file', file)
  const auth = useAuthStore()
  const res = await fetch('/api/ai/import-file', { method: 'POST', headers: { Authorization: `Bearer ${auth.token}` }, body: formData })
  const data = await res.json()
  if (res.ok) {
    fileUploadMsg.value = `解析成功，提取 ${data.original_text?.length || 0} 字`
    extractedText.value = data.original_text || data.body
    // If AI already processed it
    if (data.title) {
      result.value = { title: data.title, body: data.body, category: data.category, mood: data.mood, suggested_tags: data.suggested_tags || [] }
    }
  } else {
    fileUploadMsg.value = data.detail || '解析失败'
  }
}

function fileProcessText() {
  inputText.value = extractedText.value
  mode.value = 'text'
  extractText.value = ''
}

async function processExtractedText() {
  if (!extractedText.value.trim() || loading.value) return
  inputText.value = extractedText.value
  await processText()
}

import { useAuthStore } from '../stores/auth'

async function processText() {
  if (!inputText.value.trim() || loading.value) return
  loading.value = true
  const { data } = await api.post('/ai/import', { text: inputText.value })
  if (data) {
    result.value = {
      title: data.title || '',
      body: data.body || inputText.value,
      category: data.category || null,
      mood: data.mood || null,
      suggested_tags: data.suggested_tags || [],
      content_type: data.content_type || '',
    }
  }
  loading.value = false
}

// Voice recording
const recording = ref(false)
const elapsed = ref(0)
let recognition = null
let timer = null

function toggleRecording() {
  if (recording.value) {
    recognition?.stop()
    clearInterval(timer)
    recording.value = false
    return
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SpeechRecognition) {
    inputText.value = '[浏览器不支持语音识别，请用 Chrome]'
    return
  }

  recognition = new SpeechRecognition()
  recognition.lang = 'zh-CN'
  recognition.interimResults = true
  recognition.continuous = true

  let finalText = ''
  recognition.onresult = (e) => {
    let interim = ''
    for (let i = e.resultIndex; i < e.results.length; i++) {
      if (e.results[i].isFinal) finalText += e.results[i][0].transcript
      else interim += e.results[i][0].transcript
    }
    inputText.value = finalText + interim
  }
  recognition.onend = () => {
    recording.value = false
    clearInterval(timer)
  }

  recognition.start()
  recording.value = true
  elapsed.value = 0
  timer = setInterval(() => { elapsed.value++ }, 1000)
}

// Screen recording
const screenRecording = ref(false)
let mediaRecorder = null
let audioChunks = []

async function toggleScreen() {
  if (screenRecording.value) {
    mediaRecorder?.stop()
    screenRecording.value = false
    return
  }

  try {
    const stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true })
    mediaRecorder = new MediaRecorder(stream, { mimeType: 'video/webm' })
    audioChunks = []

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data)
    }
    mediaRecorder.onstop = () => {
      stream.getTracks().forEach(t => t.stop())
      // After recording, prompt user to describe what they recorded
      inputText.value = '[录屏已保存。请在此描述录屏中的内容，或切换到"语音"模式用麦克风录制讲解。]'
    }

    mediaRecorder.start()
    screenRecording.value = true
  } catch (e) {
    inputText.value = '[录屏功能需要浏览器权限，请在弹出窗口中选择要分享的屏幕]'
  }
}

// Save
async function saveAsPractice() {
  if (!result.value) return
  saving.value = 'practice'
  const { error } = await api.post('/practices', {
    title: result.value.title,
    body: result.value.body,
    mood: result.value.mood,
    category: result.value.category,
    practice_date: new Date().toISOString().slice(0, 10),
  })
  saving.value = false
  if (!error) {
    result.value = null
    inputText.value = ''
    router.push('/practice')
  }
}

async function saveAsContent() {
  if (!result.value) return
  saving.value = 'content'
  const { error } = await api.post('/contents', {
    title: result.value.title,
    body: result.value.body,
    category: 'quote',
    source: '智能导入',
  })
  saving.value = false
  if (!error) {
    result.value = null
    inputText.value = ''
    router.push('/library')
  }
}
</script>
