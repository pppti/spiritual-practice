<template>
  <div class="px-4 py-4 pb-4">
    <div v-if="loading" class="text-center py-12 text-sage-400">加载中...</div>
    <template v-else-if="content">
      <!-- Toolbar -->
      <div class="flex gap-2 mb-4">
        <button @click="$router.back()" class="flex-1 py-2.5 bg-sage-200 text-sage-700 rounded-lg text-sm hover:bg-sage-300 transition-colors">返回</button>
        <button v-if="toc.length" @click="showToc = !showToc" class="px-4 py-2.5 bg-sage-200 text-sage-700 rounded-lg text-sm hover:bg-sage-300 transition-colors">📑 目录</button>
        <button @click="handleDelete" class="px-4 py-2.5 bg-vermilion-500 text-white rounded-lg text-sm hover:bg-vermilion-600 transition-colors">删除</button>
      </div>

      <!-- TOC Modal -->
      <div v-if="showToc" class="fixed inset-0 bg-ink-900/40 z-50 flex justify-end" @click.self="showToc=false">
        <div class="bg-white w-72 h-full overflow-y-auto shadow-lg p-4">
          <h3 class="font-bold text-sage-800 mb-3">目录</h3>
          <div class="space-y-1">
            <button v-for="(item, i) in toc" :key="i" @click="scrollToAnchor(item.id); showToc=false"
              class="block w-full text-left text-sm py-2 px-2 rounded hover:bg-sage-100 text-sage-700 transition-colors"
              :class="{ 'pl-6 text-xs text-sage-500': item.level > 1 }">
              {{ item.title }}
            </button>
          </div>
        </div>
      </div>

      <!-- Content -->
      <div class="bg-white rounded-xl p-5 border border-sage-200 shadow-sm">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs px-2 py-0.5 bg-sage-100 text-sage-600 rounded-full">{{ categoryNames[content.category] }}</span>
          <span v-if="(content.body||'').length > 3000" class="text-xs text-sage-500">
            {{ ((content.body || '').length / 1000).toFixed(0) }}K字
          </span>
        </div>
        <h1 class="text-xl font-serif font-bold text-sage-900 mb-3">{{ content.title }}</h1>
        <div class="font-serif text-sage-700 leading-relaxed whitespace-pre-wrap text-base" ref="contentBody">
          <template v-for="(block, i) in contentBlocks" :key="i">
            <h3 v-if="block.isHeading" :id="'anchor-'+i"
              class="text-lg font-bold text-sage-800 mt-6 mb-2 border-b border-sage-200 pb-1"
              :class="{ 'text-base': block.level > 1 }">
              {{ block.text }}
            </h3>
            <p v-else class="mb-3">{{ block.text }}</p>
          </template>
        </div>
        <p v-if="content.source" class="text-sm text-sage-500 mt-4 pt-4 border-t border-sage-100">—— {{ content.source }}</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApi } from '../composables/useApi'

const route = useRoute()
const router = useRouter()
const api = useApi()
const content = ref(null)
const loading = ref(true)
const showToc = ref(false)

const categoryNames = { quote: '语录', passage: '段落', sutra: '经文', classic: '经典', book: '书籍', verse: '诗词' }

const toc = computed(() => {
  if (!content.value?.body) return []
  const lines = content.value.body.split('\n')
  const headings = []
  // Match patterns like: 第X章, 第一章, Chapter, 一、, (一), 1.1, etc.
  const patterns = [
    /^(第[一二三四五六七八九十百千\d]+章[^\n]*)/,
    /^(第[一二三四五六七八九十百千\d]+节[^\n]*)/,
    /^([一二三四五六七八九十]+、[^\n]+)/,
    /^(Chapter\s+\d+[^\n]*)/i,
    /^(\d+\.\s+[^\n]+)/,
  ]
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line || line.length > 100) continue
    for (const pat of patterns) {
      const m = line.match(pat)
      if (m) {
        headings.push({ id: 'anchor-' + headings.length, title: m[1], level: pat.toString().includes('节') ? 2 : 1 })
        break
      }
    }
  }
  return headings
})

const contentBlocks = computed(() => {
  if (!content.value?.body) return [{ text: '', isHeading: false }]
  // Split body into blocks: headings become clickable anchors, rest is text
  const body = content.value.body
  const lines = body.split('\n')
  const blocks = []
  let currentText = ''

  const isHeading = (line) => {
    const trimmed = line.trim()
    if (!trimmed || trimmed.length > 100) return false
    return /^(第[一二三四五六七八九十百千\d]+[章节][^\n]*)/.test(trimmed) ||
           /^([一二三四五六七八九十]+、[^\n]+)/.test(trimmed) ||
           /^(Chapter\s+\d+[^\n]*)/i.test(trimmed)
  }

  for (const line of lines) {
    if (isHeading(line)) {
      if (currentText.trim()) {
        blocks.push({ text: currentText, isHeading: false })
        currentText = ''
      }
      blocks.push({ text: line.trim(), isHeading: true, level: line.includes('节') ? 2 : 1 })
    } else {
      currentText += line + '\n'
    }
  }
  if (currentText.trim()) blocks.push({ text: currentText, isHeading: false })
  return blocks
})

function scrollToAnchor(id) {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
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
