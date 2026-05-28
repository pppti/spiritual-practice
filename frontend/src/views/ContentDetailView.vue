<template>
  <div class="px-4 py-4 pb-4">
    <div v-if="loading" class="text-center py-12 text-sage-400">加载中...</div>
    <template v-else-if="content">
      <div class="flex gap-2 mb-4">
        <button @click="$router.back()" class="flex-1 py-2.5 bg-sage-200 text-sage-700 rounded-lg text-sm hover:bg-sage-300 transition-colors">返回</button>
        <button v-if="tocItems.length" @click="showToc = !showToc" class="px-4 py-2.5 bg-sage-200 text-sage-700 rounded-lg text-sm hover:bg-sage-300 transition-colors">📑 目录</button>
        <button @click="handleDelete" class="px-4 py-2.5 bg-vermilion-500 text-white rounded-lg text-sm hover:bg-vermilion-600 transition-colors">删除</button>
      </div>

      <!-- TOC Sidebar -->
      <div v-if="showToc" class="fixed inset-0 z-50 flex justify-end" style="background:rgba(0,0,0,0.3)" @click.self="showToc=false">
        <div class="bg-white w-72 h-full overflow-y-auto shadow-lg p-4 safe-bottom" style="padding-bottom:120px">
          <h3 class="font-bold text-sage-800 mb-3">目录</h3>
          <div class="space-y-1">
            <button v-for="(item, i) in tocItems" :key="i" @click="jumpToPage(item.page); showToc=false"
              class="block w-full text-left text-sm py-2 px-2 rounded hover:bg-sage-100 text-sage-700 transition-colors"
              :class="{ 'pl-6 text-xs text-slate-500': item.level > 0 }">
              <span>{{ item.title }}</span>
              <span class="text-xs text-sage-400 ml-1">P{{ item.page }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Book Content -->
      <div class="bg-white rounded-xl p-5 border border-sage-200 shadow-sm">
        <span class="text-xs px-2 py-0.5 bg-sage-100 text-sage-600 rounded-full">{{ categoryNames[content.category] }}</span>
        <h1 class="text-xl font-serif font-bold text-sage-900 mt-2 mb-4">{{ content.title }}</h1>
        <div class="font-serif text-sage-700 leading-relaxed whitespace-pre-wrap text-base" v-html="renderedBody"></div>
        <p v-if="content.source" class="text-sm text-sage-500 mt-4 pt-4 border-t border-sage-100">—— {{ content.source }}</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApi } from '../composables/useApi'

const route = useRoute()
const router = useRouter()
const api = useApi()
const content = ref(null)
const loading = ref(true)
const showToc = ref(false)

const categoryNames = { quote: '语录', passage: '段落', sutra: '经文', classic: '经典', book: '书籍', verse: '诗词' }

// Parse TOC from 【目录导航】... --- section
const tocItems = computed(() => {
  if (!content.value?.body) return []
  const body = content.value.body
  const navMatch = body.match(/【目录导航】\n([\s\S]*?)\n---/)
  if (!navMatch) return []
  const lines = navMatch[1].split('\n')
  const items = []
  for (const line of lines) {
    const m = line.match(/^(\s*)(.+?)\s*→\s*P(\d+)/)
    if (m) {
      items.push({
        level: m[1].length / 2,
        title: m[2].trim(),
        page: parseInt(m[3])
      })
    }
  }
  return items
})

// Render body after ---, wrapping page markers as jump targets
const renderedBody = computed(() => {
  if (!content.value?.body) return ''
  const parts = content.value.body.split('\n---\n', 2)
  const body = parts.length > 1 ? parts[1] : parts[0]
  // Make page anchors visible and styled
  return body
    .replace(/<a id="page(\d+)"><\/a>/g, '<span id="page$1" class="page-marker"></span>')
    .replace(/\[第(\d+)页\]/g, '<span class="text-xs text-sage-400 bg-sage-50 px-1 rounded select-none">[$1]</span>')
    .replace(/\n/g, '<br>')
})

function jumpToPage(page) {
  showToc.value = false
  const el = document.getElementById('page' + page)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

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

<style scoped>
.page-marker { display: block; height: 1px; }
</style>
