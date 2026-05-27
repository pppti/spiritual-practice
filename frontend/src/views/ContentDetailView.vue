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
            <button v-for="(item, i) in toc" :key="i" @click="jumpToHeading(item.title); showToc=false"
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
        <div class="font-serif text-sage-700 leading-relaxed whitespace-pre-wrap text-base" ref="contentBody" v-html="renderedBody"></div>
        <p v-if="content.source" class="text-sm text-slate-500 mt-4 pt-4 border-t border-sage-100">—— {{ content.source }}</p>
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
const contentBody = ref(null)

const categoryNames = { quote: '语录', passage: '段落', sutra: '经文', classic: '经典', book: '书籍', verse: '诗词' }

function slugify(text) {
  // Simple hash that avoids Chinese chars in DOM IDs
  let h = 0
  for (let i = 0; i < text.length; i++) h = ((h << 5) - h + text.charCodeAt(i)) | 0
  return 'h' + Math.abs(h).toString(36)
}

const toc = computed(() => {
  if (!content.value?.body) return []
  const lines = content.value.body.split('\n')
  const headings = []
  const seen = new Set()
  const patterns = [
    { regex: /^(第[一二三四五六七八九十百千\d]+章[^\n]*)/, level: 1 },
    { regex: /^(第[一二三四五六七八九十百千\d]+节[^\n]*)/, level: 2 },
    { regex: /^([一二三四五六七八九十]+、[^\n]{2,})/, level: 1 },
    { regex: /^(Chapter\s+\d+[^\n]*)/i, level: 1 },
    { regex: /^(（[一二三四五六七八九十]）[^\n]+)/, level: 2 },
  ]
  for (const line of lines) {
    const t = line.trim()
    if (!t || t.length > 120 || t.length < 3) continue
    for (const { regex, level } of patterns) {
      const m = t.match(regex)
      if (m && !seen.has(m[1])) {
        seen.add(m[1])
        headings.push({ title: m[1].slice(0, 80), level, id: slugify(m[1]) })
        break
      }
    }
  }
  return headings
})

const renderedBody = computed(() => {
  if (!content.value?.body) return ''
  const lines = content.value.body.split('\n')
  const isHeading = (line) => {
    const t = line.trim()
    if (!t || t.length > 120) return false
    return /^(第[一二三四五六七八九十百千\d]+[章节卷部篇])/.test(t) ||
           /^([一二三四五六七八九十]+[、\.\s])/.test(t) ||
           /^(（[一二三四五六七八九十]）)/.test(t) ||
           /^(Chapter\s+\d+)/i.test(t)
  }

  let html = ''
  for (const line of lines) {
    const t = line.trim()
    if (!t) { html += '<br>'; continue }
    if (isHeading(line)) {
      const id = slugify(t)
      html += `<h3 id="${id}" style="font-weight:bold;font-size:1.1em;margin-top:1.5em;margin-bottom:0.5em;padding-bottom:4px;border-bottom:1px solid #d1d7c9;color:#2d3a26">${escapeHtml(t)}</h3>`
    } else {
      html += `<p style="margin-bottom:0.8em">${escapeHtml(t)}</p>`
    }
  }
  return html
})

function escapeHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
}

function jumpToHeading(title) {
  const id = slugify(title)
  const el = document.getElementById(id)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

onMounted(async () => {
  const { data } = await api.get(`/contents/${route.params.id}`)
  if (data) content.value = data
  loading.value = false

  // If navigated with a hash (from daily reading), scroll to it
  await nextTick()
  const hash = route.hash?.replace('#','')
  if (hash) {
    setTimeout(() => jumpToHeading(decodeURIComponent(hash)), 500)
  }
})

async function handleDelete() {
  if (!confirm('确定删除这条内容吗？')) return
  await api.delete(`/contents/${route.params.id}`)
  router.push('/library')
}
</script>
