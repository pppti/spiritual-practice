<template>
  <div class="px-4 py-4 pb-4">
    <div v-if="loading" class="text-center py-12 text-sage-400">加载中...</div>
    <template v-else-if="content">
      <div class="bg-white rounded-xl p-5 border border-sage-200 shadow-sm mb-4">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs px-2 py-0.5 bg-sage-100 text-sage-600 rounded-full">{{ categoryNames[content.category] }}</span>
          <button @click="expanded = !expanded" class="text-xs text-sage-500 underline">{{ expanded ? '收起' : '阅读全文' }}</button>
        </div>
        <h1 class="text-xl font-serif font-bold text-sage-900 mb-3">{{ content.title }}</h1>
        <div class="font-serif text-sage-700 leading-relaxed whitespace-pre-wrap" :class="expanded ? '' : 'max-h-[60vh] overflow-hidden relative'">
          <p class="text-base">{{ expanded ? content.body : (content.body || '').slice(0, 3000) }}</p>
          <div v-if="!expanded && (content.body || '').length > 3000" class="absolute bottom-0 inset-x-0 h-20 bg-gradient-to-t from-white to-transparent pointer-events-none"></div>
        </div>
        <p v-if="!expanded && (content.body || '').length > 3000" class="text-center mt-1">
          <button @click="expanded = true" class="text-sm text-sage-600 underline">展开全部（{{ ((content.body || '').length / 1000).toFixed(0) }}K字）</button>
        </p>
        <p v-if="content.source" class="text-sm text-sage-500 mt-2">—— {{ content.source }}</p>
      </div>

      <div class="flex gap-3 mb-8">
        <button @click="$router.back()"
          class="flex-1 py-3 border border-sage-400 text-sage-700 rounded-lg text-sm hover:bg-sage-100 transition-colors">
          返回
        </button>
        <button @click="handleDelete"
          class="flex-1 py-3 border border-vermilion-500 text-vermilion-500 rounded-lg text-sm hover:bg-vermilion-50 transition-colors">
          删除
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApi } from '../composables/useApi'

const route = useRoute()
const router = useRouter()
const api = useApi()
const content = ref(null)
const loading = ref(true)
const expanded = ref(false)

const categoryNames = { quote: '语录', passage: '段落', sutra: '经文', classic: '经典', book: '书籍', verse: '诗词' }

onMounted(async () => {
  const { data } = await api.get(`/contents/${route.params.id}`)
  if (data) content.value = data
  loading.value = false
})

async function handleDelete() {
  if (!confirm('确定删除这条内容吗？')) return
  await api.delete(`/contents/${route.params.id}`)
  router.push('/library')
}
</script>
