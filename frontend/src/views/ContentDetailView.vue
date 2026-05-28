<template>
  <div class="px-4 py-4 pb-4">
    <div v-if="loading" class="text-center py-12 text-sage-400">加载中...</div>
    <template v-else-if="content">
      <div class="flex gap-2 mb-4">
        <button @click="$router.back()" class="flex-1 py-2.5 bg-sage-200 text-sage-700 rounded-lg text-sm hover:bg-sage-300 transition-colors">返回</button>
        <button v-if="toc.length" @click="showToc = !showToc" class="px-4 py-2.5 bg-sage-200 text-sage-700 rounded-lg text-sm hover:bg-sage-300 transition-colors">📑 目录</button>
        <button @click="handleDelete" class="px-4 py-2.5 bg-vermilion-500 text-white rounded-lg text-sm hover:bg-vermilion-600 transition-colors">删除</button>
      </div>

      <div v-if="showToc" class="fixed inset-0 z-50 flex justify-end" style="background:rgba(0,0,0,0.3)" @click.self="showToc=false">
        <div class="bg-white w-72 h-full overflow-y-auto shadow-lg p-4" style="padding-bottom:120px">
          <h3 class="font-bold text-sage-800 mb-3">目录</h3>
          <div class="space-y-1">
            <button v-for="(item, i) in toc" :key="i" @click="jumpToHeading(i); showToc=false"
              class="block w-full text-left text-sm py-2 px-2 rounded hover:bg-sage-100 text-sage-700 transition-colors"
              :class="{ 'pl-6 text-xs text-slate-500': item.level > 1 }">
              {{ item.title }}
            </button>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl p-5 border border-sage-200 shadow-sm">
        <span class="text-xs px-2 py-0.5 bg-sage-100 text-sage-600 rounded-full">{{ categoryNames[content.category] }}</span>
        <h1 class="text-xl font-serif font-bold text-sage-900 mt-2 mb-4">{{ content.title }}</h1>
        <div class="font-serif text-sage-700 leading-relaxed whitespace-pre-wrap text-base" ref="contentBody">
          <template v-for="(block, i) in contentBlocks" :key="i">
            <h3 v-if="block.isHeading" :id="'sec-'+i"
              class="text-lg font-bold text-sage-800 mt-6 mb-2 border-b border-sage-200 pb-1"
              :class="{ 'text-base': block.level > 1 }">
              {{ block.text }}
            </h3>
            <p v-else class="mb-3">{{ block.text }}</p>
          </template>
        </div>
        <p v-if="content.source" class="text-sm text-slate-500 mt-4 pt-4 border-t border-sage-100">—— {{ content.source }}</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApi } from '../composables/useApi'

const route = useRoute()
const router = useRouter()
const api = useApi()
const content = ref(null)
const loading = ref(true)
const showToc = ref(false)
const contentBody = ref(null)

const categoryNames = { quote: '语录', passage: '段落', sutra: '经文', classic: '经典', book: '书籍', verse: '诗词' }

function isHeadingLine(line) {
  const t = line.trim()
  if (!t || t.length > 120) return false
  return /^(第[一二三四五六七八九十百千\d]+[章节卷部篇])/.test(t) ||
         /^([一二三四五六七八九十]+[、\.\s])/.test(t) ||
         /^(（[一二三四五六七八九十]）)/.test(t) ||
         /^(Chapter\s+\d+)/i.test(t)
}

function getHeadingLevel(line) {
  const t = line.trim()
  if (/节/.test(t)) return 2
  return 1
}

const toc = computed(() => {
  if (!content.value?.body) return []
  const lines = content.value.body.split('\n')
  const headings = []
  const seen = new Set()
  for (const line of lines) {
    if (!isHeadingLine(line)) continue
    const t = line.trim()
    if (seen.has(t)) continue
    seen.add(t)
    headings.push({
      title: t.slice(0, 80),
      level: getHeadingLevel(line),
      index: headings.length // maps to contentBlock index later
    })
  }
  return headings
})

const contentBlocks = computed(() => {
  if (!content.value?.body) return [{ text: '', isHeading: false }]
  const lines = content.value.body.split('\n')
  const blocks = []
  let currentText = ''
  let headingIdx = 0

  for (const line of lines) {
    if (isHeadingLine(line)) {
      if (currentText.trim()) {
        blocks.push({ text: currentText, isHeading: false })
        currentText = ''
      }
      const t = line.trim()
      blocks.push({ text: t, isHeading: true, level: getHeadingLevel(line), headingIdx: headingIdx++ })
    } else {
      currentText += line + '\n'
    }
  }
  if (currentText.trim()) blocks.push({ text: currentText, isHeading: false })
  return blocks
})

// Build map: TOC heading index -> contentBlock index
const tocToBlockIndex = computed(() => {
  const map = {}
  let hi = 0
  contentBlocks.value.forEach((block, bi) => {
    if (block.isHeading) {
      map[hi] = bi
      hi++
    }
  })
  return map
})

function jumpToHeading(tocIndex) {
  showToc.value = false
  const blockIndex = tocToBlockIndex.value[tocIndex]
  if (blockIndex === undefined) return
  const el = document.getElementById('sec-' + blockIndex)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

onMounted(async () => {
  const { data } = await api.get(`/contents/${route.params.id}`)
  if (data) content.value = data
  loading.value = false

  // If navigated with hash (from daily reading), scroll on load
  const hash = route.hash?.replace('#', '')
  if (hash) {
    await nextTick()
    // Find TOC index matching the hash text
    setTimeout(() => {
      const idx = toc.value.findIndex(item => item.title === decodeURIComponent(hash))
      if (idx >= 0) jumpToHeading(idx)
    }, 300)
  }
})

async function handleDelete() {
  if (!confirm('确定删除这条内容吗？')) return
  await api.delete(`/contents/${route.params.id}`)
  router.push('/library')
}
</script>
