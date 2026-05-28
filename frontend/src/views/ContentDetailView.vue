<template>
  <div class="px-4 py-4 pb-4">
    <div v-if="loading" class="text-center py-12 text-sage-400">加载中...</div>
    <template v-else-if="content">
      <div class="flex gap-2 mb-4">
        <button @click="$router.back()" class="flex-1 py-2.5 bg-sage-200 text-sage-700 rounded-lg text-sm hover:bg-sage-300 transition-colors">返回</button>
        <button v-if="tocItems.length" @click="showToc = !showToc" class="px-4 py-2.5 bg-sage-200 text-sage-700 rounded-lg text-sm hover:bg-sage-300 transition-colors">目录</button>
        <button @click="handleDelete" class="px-4 py-2.5 bg-vermilion-500 text-white rounded-lg text-sm hover:bg-vermilion-600 transition-colors">删除</button>
      </div>

      <div v-if="showToc" class="fixed inset-0 z-50 flex justify-end" style="background:rgba(0,0,0,0.3)" @click.self="showToc=false">
        <div class="bg-white w-72 h-full overflow-y-auto shadow-lg p-4" style="padding-bottom:120px">
          <h3 class="font-bold text-sage-800 mb-3">目录</h3>
          <div class="space-y-1">
            <button v-for="(item, i) in tocItems" :key="i" @click="jumpToSection(item.title); showToc=false"
              class="block w-full text-left text-sm py-2 px-2 rounded hover:bg-sage-100 text-sage-700 transition-colors"
              :class="{ 'pl-4 text-xs': item.level > 0 }">
              {{ item.title }}
            </button>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl p-5 border border-sage-200 shadow-sm" ref="contentBox">
        <span class="text-xs px-2 py-0.5 bg-sage-100 text-sage-600 rounded-full">{{ categoryNames[content.category] }}</span>
        <h1 class="text-xl font-serif font-bold text-sage-900 mt-2 mb-4">{{ content.title }}</h1>
        <div class="font-serif text-sage-700 leading-relaxed whitespace-pre-wrap text-base" ref="bodyEl" v-html="displayBody"></div>
        <p v-if="content.source" class="text-sm text-slate-500 mt-4 pt-4 border-t border-sage-100">—— {{ content.source }}</p>
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
const bodyEl = ref(null)

const categoryNames = { quote: '语录', passage: '段落', sutra: '经文', classic: '经典', book: '书籍', verse: '诗词' }

const TOC_MARKER = '【目录导航】'

const tocItems = computed(() => {
  if (!content.value?.body) return []
  const body = content.value.body
  const tocStart = body.indexOf(TOC_MARKER)
  if (tocStart === -1) return []
  const tocEnd = body.indexOf('\n---', tocStart)
  if (tocEnd === -1) return []
  const tocSection = body.slice(tocStart + TOC_MARKER.length + 1, tocEnd)
  return tocSection.split('\n').filter(l => l.trim()).map(l => {
    const trimmed = l.trim()
    const leadingSpaces = l.length - l.trimStart().length
    return { title: trimmed, level: Math.floor(leadingSpaces / 2) }
  })
})

const displayBody = computed(() => {
  if (!content.value?.body) return ''
  const body = content.value.body
  const tocStart = body.indexOf(TOC_MARKER)
  if (tocStart === -1) return body.replace(/\n/g, '<br>')
  const tocEnd = body.indexOf('\n---', tocStart)
  if (tocEnd === -1) return body.replace(/\n/g, '<br>')
  return body.slice(tocEnd + 4).replace(/\n/g, '<br>')
})

function jumpToSection(title) {
  showToc.value = false
  const el = bodyEl.value
  if (!el) return
  // Search for the title text in the rendered content
  const searchKey = title.slice(0, 15).replace(/^\s+/, '')
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)
  let node
  while (node = walker.nextNode()) {
    const idx = node.textContent.indexOf(searchKey)
    if (idx >= 0) {
      const range = document.createRange()
      range.setStart(node, idx)
      range.collapse(true)
      range.startContainer.parentElement?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      break
    }
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
