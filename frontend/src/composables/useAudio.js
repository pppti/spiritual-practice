import { ref, shallowRef } from 'vue'

const tracks = ref([])
const audioContext = shallowRef(null)

function getContext() {
  if (!audioContext.value) {
    audioContext.value = new (window.AudioContext || window.webkitAudioContext)()
  }
  if (audioContext.value.state === 'suspended') {
    audioContext.value.resume()
  }
  return audioContext.value
}

export function useAudio() {
  function addTrack(trackData) {
    const existing = tracks.value.find(t => t.id === trackData.id)
    if (existing) return existing

    const audio = new Audio()
    audio.src = `/api/white-noise/stream/${trackData.id}`
    audio.loop = true
    audio.crossOrigin = 'anonymous'
    audio.preload = 'auto'

    let gainNode = null
    try {
      const ctx = getContext()
      const source = ctx.createMediaElementSource(audio)
      gainNode = ctx.createGain()
      gainNode.gain.value = 0.5
      source.connect(gainNode)
      gainNode.connect(ctx.destination)
    } catch (e) {
      // Web Audio API routing failed, use audio element directly
      audio.volume = 0.5
    }

    const entry = {
      id: trackData.id,
      name: trackData.name_cn || trackData.name,
      category: trackData.category,
      audio,
      gainNode,
      playing: ref(false),
      volume: ref(0.5),
    }

    audio.addEventListener('play', () => { entry.playing.value = true })
    audio.addEventListener('pause', () => { entry.playing.value = false })
    audio.addEventListener('error', (e) => {
      console.error('Audio error:', e)
      entry.playing.value = false
    })

    tracks.value.push(entry)
    return entry
  }

  function removeTrack(id) {
    const idx = tracks.value.findIndex(t => t.id === id)
    if (idx === -1) return
    const entry = tracks.value[idx]
    entry.audio.pause()
    entry.audio.src = ''
    if (entry.gainNode) entry.gainNode.disconnect()
    tracks.value.splice(idx, 1)
  }

  function togglePlay(id) {
    const entry = tracks.value.find(t => t.id === id)
    if (!entry) return
    if (entry.audio.paused) {
      const ctx = audioContext.value
      if (ctx && ctx.state === 'suspended') ctx.resume()
      entry.audio.play().catch(err => {
        console.error('Play failed:', err)
        entry.playing.value = false
      })
    } else {
      entry.audio.pause()
    }
  }

  function setVolume(id, vol) {
    const entry = tracks.value.find(t => t.id === id)
    if (!entry) return
    const v = parseFloat(vol)
    if (entry.gainNode) {
      entry.gainNode.gain.value = v
    } else {
      entry.audio.volume = v
    }
    entry.volume.value = v
  }

  function stopAll() {
    tracks.value.forEach(t => {
      t.audio.pause()
      t.playing.value = false
    })
    tracks.value = []
  }

  return { tracks, addTrack, removeTrack, togglePlay, setVolume, stopAll }
}
