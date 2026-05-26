<template>
  <div class="h-[calc(100vh-7rem)] flex flex-col">
    <!-- Mode toggle -->
    <div class="px-4 py-2 flex gap-2 border-b border-sage-100">
      <button @click="mode = 'general'" class="px-3 py-1 text-xs rounded-full transition-colors"
        :class="mode === 'general' ? 'bg-sage-200 text-sage-800' : 'text-sage-500'">
        自由问答
      </button>
      <button @click="mode = 'analysis'" class="px-3 py-1 text-xs rounded-full transition-colors"
        :class="mode === 'analysis' ? 'bg-sage-200 text-sage-800' : 'text-sage-500'">
        个人分析
      </button>
      <button v-if="conversations.length" @click="showHistory = !showHistory"
        class="ml-auto px-3 py-1 text-xs rounded-full text-sage-500 border border-sage-200">
        {{ showHistory ? '返回对话' : '历史' }}
      </button>
    </div>

    <!-- History view -->
    <div v-if="showHistory" class="flex-1 overflow-y-auto px-4 py-2 space-y-1">
      <button v-for="c in conversations" :key="c.id"
        @click="loadConversation(c.id)"
        class="w-full text-left px-3 py-2 rounded-lg hover:bg-sage-100 transition-colors">
        <p class="text-sm text-sage-800 truncate">{{ c.title }}</p>
        <p class="text-xs text-sage-400">{{ c.created_at.slice(0, 16).replace('T', ' ') }}</p>
      </button>
      <button v-if="!conversations.length" @click="newChat"
        class="w-full text-center py-4 text-sm text-sage-500">
        开始新对话
      </button>
    </div>

    <!-- Chat view -->
    <div v-else class="flex-1 flex flex-col">
      <!-- Messages -->
      <div ref="chatContainer" class="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        <div v-if="messages.length === 0" class="text-center py-12">
          <p class="text-sage-400 text-sm mb-2">
            {{ mode === 'general' ? '与觉明法师对话，探讨修行之道' : '分析你的修行数据，获得个性化指引' }}
          </p>
          <div class="flex flex-wrap gap-2 justify-center">
            <button v-for="q in suggestions" :key="q" @click="sendMessage(q)"
              class="px-3 py-1.5 text-xs bg-sage-100 text-sage-600 rounded-full hover:bg-sage-200 transition-colors">
              {{ q }}
            </button>
          </div>
        </div>

        <div v-for="(msg, i) in messages" :key="i" class="flex"
          :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
          <div class="max-w-[85%] rounded-xl px-4 py-2.5 text-sm leading-relaxed"
            :class="msg.role === 'user'
              ? 'bg-sage-800 text-white'
              : 'bg-white border border-sage-200 text-sage-700'">
            {{ msg.content }}
          </div>
        </div>

        <div v-if="loading" class="flex justify-start">
          <div class="bg-white border border-sage-200 rounded-xl px-4 py-3">
            <span class="inline-flex gap-1">
              <span class="w-1.5 h-1.5 bg-sage-400 rounded-full animate-bounce" style="animation-delay:0s"></span>
              <span class="w-1.5 h-1.5 bg-sage-400 rounded-full animate-bounce" style="animation-delay:0.15s"></span>
              <span class="w-1.5 h-1.5 bg-sage-400 rounded-full animate-bounce" style="animation-delay:0.3s"></span>
            </span>
          </div>
        </div>
      </div>

      <!-- Input -->
      <div class="px-4 py-3 border-t border-sage-100">
        <form @submit.prevent="sendMessage()" class="flex gap-2">
          <input v-model="input" type="text" placeholder="输入问题..."
            class="flex-1 px-4 py-2.5 rounded-xl border border-sage-200 text-sm focus:outline-none focus:border-sage-500"
            :disabled="loading" />
          <button type="submit" :disabled="!input.trim() || loading"
            class="px-5 py-2.5 bg-sage-800 text-white rounded-xl text-sm hover:bg-sage-700 disabled:opacity-40 transition-colors">
            发送
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useApi } from '../composables/useApi'

const api = useApi()
const mode = ref('general')
const input = ref('')
const loading = ref(false)
const messages = ref([])
const conversations = ref([])
const showHistory = ref(false)
const conversationId = ref(null)
const chatContainer = ref(null)

const suggestions = ref([
  '如何应对日常的焦虑？',
  '修行应该如何坚持？',
  '推荐一本适合初学者的经典',
  '冥想时总是走神怎么办？',
])

async function sendMessage(text) {
  const msg = text || input.value.trim()
  if (!msg || loading.value) return

  messages.value.push({ role: 'user', content: msg })
  input.value = ''
  loading.value = true

  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }

  const { data, error } = await api.post('/ai/chat', {
    conversation_id: conversationId.value,
    message: msg,
    mode: mode.value,
  })

  if (data) {
    conversationId.value = data.conversation_id
    messages.value.push({ role: 'assistant', content: data.reply })
  } else {
    messages.value.push({ role: 'assistant', content: '抱歉，出了点问题，请稍后再试。' })
  }

  loading.value = false
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

async function loadConversation(id) {
  const { data } = await api.get(`/ai/conversations/${id}`)
  if (data) {
    conversationId.value = data.id
    messages.value = data.messages.map(m => ({ role: m.role, content: m.content }))
    showHistory.value = false
  }
}

function newChat() {
  conversationId.value = null
  messages.value = []
  showHistory.value = false
}

onMounted(async () => {
  const { data } = await api.get('/ai/conversations')
  if (data) conversations.value = data.items
})
</script>

<style scoped>
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-6px); }
}
.animate-bounce { animation: bounce 1.4s infinite; }
</style>
