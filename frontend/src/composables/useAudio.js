import { ref } from 'vue'

const tracks = ref([])

export function useAudio() {
  function addTrack(trackData) {
    const existing = tracks.value.find(t => t.id === trackData.id)
    if (existing) return existing

    const audio = new Audio()
    audio.src = `/api/white-noise/stream/${trackData.id}`
    audio.loop = true
    audio.volume = 0.5

    const entry = {
      id: trackData.id,
      name: trackData.name_cn || trackData.name,
      audio,
      playing: ref(false),
      loading: ref(false),
      error: ref(''),
      volume: ref(0.5),
    }

    audio.addEventListener('loadstart', () => { entry.loading.value = true; entry.error.value = '' })
    audio.addEventListener('canplay', () => { entry.loading.value = false })
    audio.addEventListener('play', () => { entry.playing.value = true })
    audio.addEventListener('pause', () => { entry.playing.value = false })
    audio.addEventListener('ended', () => { entry.playing.value = false })
    audio.addEventListener('error', () => {
      entry.loading.value = false
      entry.playing.value = false
      const codes = {1:'加载中断',2:'网络错误',3:'解码失败',4:'格式不支持'}
      entry.error.value = codes[audio.error?.code] || '未知错误'
    })

    tracks.value.push(entry)
    audio.load()
    return entry
  }

  function removeTrack(id) {
    const idx = tracks.value.findIndex(t => t.id === id)
    if (idx === -1) return
    const entry = tracks.value[idx]
    entry.audio.pause()
    entry.audio.src = ''
    tracks.value.splice(idx, 1)
  }

  function togglePlay(id) {
    const entry = tracks.value.find(t => t.id === id)
    if (!entry) return
    if (entry.audio.paused) {
      entry.error.value = ''
      entry.audio.load()
      entry.audio.play().catch(() => {})
    } else {
      entry.audio.pause()
    }
  }

  function setVolume(id, vol) {
    const entry = tracks.value.find(t => t.id === id)
    if (!entry) return
    entry.audio.volume = parseFloat(vol)
    entry.volume.value = entry.audio.volume
  }

  function stopAll() {
    tracks.value.forEach(t => t.audio.pause())
    tracks.value = []
  }

  return { tracks, addTrack, removeTrack, togglePlay, setVolume, stopAll }
}
