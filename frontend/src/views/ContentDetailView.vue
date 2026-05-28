<template>
  <div class="px-4 py-4 pb-4">
    <div v-if="loading" class="text-center py-12 text-sage-400">加载中...</div>
    <template v-else-if="content">
      <div class="flex gap-2 mb-4">
        <button @click="$router.back()" class="flex-1 py-2.5 bg-sage-200 text-sage-700 rounded-lg text-sm hover:bg-sage-300 transition-colors">返回</button>
        <button v-if="tocItems.length" @click="showToc = true" class="px-4 py-2.5 bg-sage-200 text-sage-700 rounded-lg text-sm hover:bg-sage-300 transition-colors">目录 ({{ tocItems.length }})</button>
        <button @click="handleDelete" class="px-4 py-2.5 bg-vermilion-500 text-white rounded-lg text-sm hover:bg-vermilion-600 transition-colors">删除</button>
      </div>

      <!-- TOC as full-screen overlay -->
      <div v-if="showToc" class="fixed inset-0 z-50 bg-white flex flex-col">
        <div class="flex items-center justify-between px-4 py-3 border-b border-sage-200">
          <h3 class="font-bold text-sage-800">目录 ({{ tocItems.length }}项)</h3>
          <button @click="showToc = false" class="text-sage-500 text-lg leading-none">&times;</button>
        </div>
        <div class="flex-1 overflow-y-auto px-4 py-2">
          <button v-for="(item, i) in tocItems" :key="i"
            @click="jumpToChapter(item.anchorId); showToc = false"
            class="block w-full text-left text-sm py-2.5 border-b border-sage-100 text-sage-700 hover:bg-sage-50 transition-colors"
            :class="{ 'pl-4 text-xs': item.level > 0 }">
            {{ item.title }}
          </button>
        </div>
      </div>

      <!-- Book body -->
      <div class="bg-white rounded-xl p-5 border border-sage-200 shadow-sm">
        <span class="text-xs px-2 py-0.5 bg-sage-100 text-sage-600 rounded-full">{{ categoryNames[content.category] }}</span>
        <h1 class="text-xl font-serif font-bold text-sage-900 mt-2 mb-4">{{ content.title }}</h1>
        <div class="font-serif text-sage-700 leading-relaxed whitespace-pre-wrap text-base" v-html="displayBody"></div>
        <p v-if="content.source" class="text-sm text-slate-500 mt-4 pt-4 border-t border-sage-100">—— {{ content.source }}</p>
      </div>

      <!-- Floating back-to-TOC button -->
      <button v-if="tocItems.length && showBackToc" @click="showToc = true"
        class="fixed bottom-24 right-4 w-12 h-12 bg-sage-800 text-white rounded-full shadow-lg flex items-center justify-center z-30 text-xs transition-all hover:bg-sage-700">
        📑
      </button>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApi } from '../composables/useApi'

const route = useRoute(); const router = useRouter(); const api = useApi()
const content = ref(null); const loading = ref(true); const showToc = ref(false); const showBackToc = ref(false)
const categoryNames = { quote: '语录', passage: '段落', sutra: '经文', classic: '经典', book: '书籍', verse: '诗词' }

const tocItems = computed(() => {
  if (!content.value?.body) return []
  const body = content.value.body
  const marker = '【目录导航】'
  const start = body.indexOf(marker)
  if (start === -1) return []
  const end = body.indexOf('\n---', start)
  if (end === -1) return []
  const section = body.slice(start + marker.length + 1, end)
  return section.split('\n').filter(l => l.trim()).map(l => {
    const trimmed = l.trim()
    const parts = trimmed.split('||')
    const title = parts[0]
    const anchorId = parts.length > 1 ? 'ch' + parts[1] : ''
    const level = Math.floor((l.length - l.trimStart().length) / 2)
    return { title, anchorId, level }
  }).filter(item => item.anchorId)
})

const displayBody = computed(() => {
  if (!content.value?.body) return ''
  const body = content.value.body
  const marker = '【目录导航】'
  const start = body.indexOf(marker)
  if (start === -1) return body.replace(/\n/g, '<br>')
  const end = body.indexOf('\n---', start)
  if (end === -1) return body.replace(/\n/g, '<br>')
  return body.slice(end + 5).replace(/\n/g, '<br>')
})

function jumpToChapter(anchorId) {
  showToc.value = false
  nextTick(() => {
    const el = document.getElementById(anchorId)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  })
}

let scrollHandler = null

onMounted(async () => {
  const { data } = await api.get(`/contents/${route.params.id}`)
  if (data) content.value = data
  loading.value = false
  scrollHandler = () => { showBackToc.value = window.scrollY > 400 }
  window.addEventListener('scroll', scrollHandler, { passive: true })
})

onUnmounted(() => {
  if (scrollHandler) window.removeEventListener('scroll', scrollHandler)
})

async function handleDelete() {
  if (!confirm('确定删除这条内容吗？')) return
  await api.delete(`/contents/${route.params.id}`)
  router.push('/library')
}
</script>
