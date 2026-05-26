<template>
  <div class="px-4 py-4">
    <div class="flex items-center justify-between mb-4">
      <h2 class="font-serif font-bold text-sage-800">修行日记</h2>
      <div class="flex gap-2">
        <button v-if="selectedIds.length" @click="summarizeSelected"
          class="px-3 py-1.5 bg-gold-400 text-white rounded-lg text-xs hover:bg-gold-500 transition-colors">
          汇总 {{ selectedIds.length }} 篇
        </button>
        <router-link to="/practice/new" class="bg-sage-800 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-sage-700 transition-colors">
          写日记
        </router-link>
      </div>
    </div>

    <!-- Summarize result -->
    <div v-if="summary" class="bg-white rounded-xl p-4 border border-gold-300 shadow-sm mb-4">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium text-gold-600">AI 汇总</span>
        <button @click="summary = ''" class="text-xs text-sage-400">关闭</button>
      </div>
      <p class="text-sm text-sage-700 leading-relaxed whitespace-pre-wrap">{{ summary }}</p>
    </div>

    <div v-if="loading" class="text-center text-sage-400 py-6">加载中...</div>
    <EmptyState v-else-if="entries.length === 0" text="还没有修行日记，开始写第一篇吧">
      <router-link to="/practice/new" class="mt-3 text-sm text-sage-600 underline">写日记</router-link>
    </EmptyState>
    <div v-else class="space-y-3">
      <div v-for="entry in entries" :key="entry.id"
        class="bg-white rounded-lg p-4 border transition-colors cursor-pointer"
        :class="selectedIds.includes(entry.id) ? 'border-gold-400 bg-gold-50' : 'border-sage-100 hover:border-sage-300'">
        <div class="flex items-center gap-2 mb-2">
          <input type="checkbox" :checked="selectedIds.includes(entry.id)"
            @click.stop @change="toggleSelect(entry.id)" class="rounded shrink-0" />
          <span class="font-medium text-sage-800 flex-1" @click="$router.push(`/practice/${entry.id}`)">{{ entry.title || '无标题' }}</span>
          <span class="text-xs text-sage-400" @click="$router.push(`/practice/${entry.id}`)">{{ entry.practice_date }}</span>
        </div>
        <p class="text-sm text-sage-500 line-clamp-3 mb-2">{{ entry.body }}</p>
        <div class="flex items-center gap-2">
          <span v-if="entry.mood" class="text-xs px-2 py-0.5 bg-sage-100 text-sage-600 rounded-full">
            {{ moodNames[entry.mood] || entry.mood }}
          </span>
          <span v-if="entry.duration_minutes" class="text-xs text-sage-400">{{ entry.duration_minutes }}分钟</span>
          <span v-if="entry.linked_contents.length" class="text-xs text-sage-400">
            关联 {{ entry.linked_contents.length }} 条内容
          </span>
        </div>
      </div>
      <div v-if="hasMore" class="text-center py-4">
        <button @click="loadMore" class="text-sm text-sage-500 hover:text-sage-700" :disabled="loadingMore">
          {{ loadingMore ? '加载中...' : '加载更多' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useApi } from '../composables/useApi'
import EmptyState from '../components/common/EmptyState.vue'

const api = useApi()
const entries = ref([])
const page = ref(1)
const total = ref(0)
const loading = ref(true)
const loadingMore = ref(false)
const selectedIds = ref([])
const summary = ref('')

const moodNames = { calm: '平静', energized: '精力充沛', scattered: '散乱', peaceful: '安宁', tired: '疲惫' }

const hasMore = ref(false)

async function fetchEntries(p) {
  const { data } = await api.get(`/practices?page=${p}&limit=20`)
  if (data) {
    if (p === 1) entries.value = data.items
    else entries.value.push(...data.items)
    total.value = data.total
    hasMore.value = entries.value.length < data.total
  }
}

function toggleSelect(id) {
  const idx = selectedIds.value.indexOf(id)
  if (idx === -1) selectedIds.value.push(id)
  else selectedIds.value.splice(idx, 1)
}

async function summarizeSelected() {
  if (!selectedIds.value.length) return
  summary.value = 'AI 正在汇总...'
  const { data } = await api.post('/ai/summarize', { practice_ids: selectedIds.value })
  summary.value = data?.summary || '汇总失败'
}

async function loadMore() {
  loadingMore.value = true
  page.value++
  await fetchEntries(page.value)
  loadingMore.value = false
}

onMounted(async () => {
  await fetchEntries(1)
  loading.value = false
})
</script>
