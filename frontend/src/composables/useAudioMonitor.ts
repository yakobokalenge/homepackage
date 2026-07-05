import { ref, onUnmounted } from 'vue'

export function useAudioMonitor() {
  const isVoiceDetected = ref(false)
  const audioLevel = ref(0)
  const isMonitoring = ref(false)
  let audioContext: AudioContext | null = null
  let analyser: AnalyserNode | null = null
  let rafId: number | null = null
  const VOICE_THRESHOLD = 30
  const SPEECH_FREQ_MIN = 80
  const SPEECH_FREQ_MAX = 3000

  function start(stream: MediaStream, onViolation: (type: string, desc: string, severity: string) => void) {
    audioContext = new AudioContext()
    const source = audioContext.createMediaStreamSource(stream)
    analyser = audioContext.createAnalyser()
    analyser.fftSize = 2048
    analyser.smoothingTimeConstant = 0.8
    source.connect(analyser)

    const dataArray = new Uint8Array(analyser.frequencyBinCount)
    const sampleRate = audioContext.sampleRate
    const binSize = sampleRate / analyser.fftSize
    const minBin = Math.floor(SPEECH_FREQ_MIN / binSize)
    const maxBin = Math.ceil(SPEECH_FREQ_MAX / binSize)
    let voiceStartTime = 0

    function check() {
      if (!analyser) return
      analyser.getByteFrequencyData(dataArray)
      let sum = 0
      for (let i = minBin; i <= maxBin && i < dataArray.length; i++) sum += dataArray[i]
      const average = sum / (maxBin - minBin + 1)
      audioLevel.value = average

      if (average > VOICE_THRESHOLD) {
        if (!isVoiceDetected.value) {
          isVoiceDetected.value = true
          voiceStartTime = Date.now()
        }
        // Only report if voice persists for 2+ seconds
        if (Date.now() - voiceStartTime > 2000) {
          onViolation('audio_detected', `Voice/noise detected (level: ${average.toFixed(1)})`, 'medium')
          voiceStartTime = Date.now() + 10000 // Don't re-report for 10s
        }
      } else {
        isVoiceDetected.value = false
      }
      rafId = requestAnimationFrame(check)
    }

    isMonitoring.value = true
    check()
  }

  function stop() {
    if (rafId) cancelAnimationFrame(rafId)
    audioContext?.close()
    audioContext = null
    analyser = null
    isMonitoring.value = false
  }

  onUnmounted(stop)

  return { isVoiceDetected, audioLevel, isMonitoring, start, stop }
}
