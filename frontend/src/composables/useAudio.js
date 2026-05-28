import { reactive, ref } from 'vue'

const tracks = ref([])

export function useAudio() {
  function addTrack(trackData) {
    const existing = tracks.value.find(t => t.id === trackData.id)
    if (existing) return existing

    const audio = new Audio()
    audio.src = `/api/white-noise/stream/${trackData.id}`
    audio.loop = true
    audio.volume = 0.5

    const entry = reactive({
      id: trackData.id,
      name: trackData.name_cn || trackData.name,
      audio,
      playing: false,
      volume: 0.5,
    })

    audio.addEventListener('play', () => { entry.playing = true })
    audio.addEventListener('pause', () => { entry.playing = false })
    audio.addEventListener('ended', () => { entry.playing = false })

    tracks.value.push(entry)
    audio.load()
    return entry
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
    entry.volume = entry.audio.volume
  }

  return { tracks, addTrack, togglePlay, setVolume }
}
