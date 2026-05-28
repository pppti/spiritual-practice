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
    audio.preload = 'auto'

    const entry = {
      id: trackData.id,
      name: trackData.name_cn || trackData.name,
      audio,
      playing: ref(false),
      volume: ref(0.5),
    }

    // Use event listeners instead of manual state tracking
    audio.addEventListener('play', () => { entry.playing.value = true })
    audio.addEventListener('pause', () => { entry.playing.value = false })

    tracks.value.push(entry)
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
    tracks.value.forEach(t => {
      t.audio.pause()
    })
    tracks.value = []
  }

  return { tracks, addTrack, removeTrack, togglePlay, setVolume, stopAll }
}
