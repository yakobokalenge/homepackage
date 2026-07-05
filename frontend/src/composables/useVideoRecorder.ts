import { ref, onUnmounted } from 'vue'
import { proctoringService } from '@/services/proctoring.service'

export function useVideoRecorder() {
  const isRecording = ref(false)
  const chunkIndex = ref(0)
  const uploadQueue = ref<{ blob: Blob; index: number; retries: number }[]>([])
  let mediaRecorder: MediaRecorder | null = null
  let retryInterval: ReturnType<typeof setInterval> | null = null

  const CHUNK_DURATION_MS = 10000 // 10 second chunks

  function start(stream: MediaStream, sessionId: string) {
    const mimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp8,opus')
      ? 'video/webm;codecs=vp8,opus' : 'video/webm'

    mediaRecorder = new MediaRecorder(stream, { mimeType, videoBitsPerSecond: 500000 })

    mediaRecorder.ondataavailable = async (event) => {
      if (event.data.size > 0) {
        const currentIndex = chunkIndex.value++
        await uploadChunk(event.data, sessionId, currentIndex)
      }
    }

    mediaRecorder.start(CHUNK_DURATION_MS)
    isRecording.value = true

    // Retry failed uploads every 5s
    retryInterval = setInterval(() => processRetryQueue(sessionId), 5000)
  }

  async function uploadChunk(blob: Blob, sessionId: string, index: number) {
    try {
      await proctoringService.uploadVideoChunk(sessionId, index, blob)
    } catch {
      uploadQueue.value.push({ blob, index, retries: 0 })
    }
  }

  async function processRetryQueue(sessionId: string) {
    const pending = [...uploadQueue.value]
    uploadQueue.value = []
    for (const item of pending) {
      if (item.retries >= 3) continue // Give up after 3 retries
      try {
        await proctoringService.uploadVideoChunk(sessionId, item.index, item.blob)
      } catch {
        uploadQueue.value.push({ ...item, retries: item.retries + 1 })
      }
    }
  }

  function stop() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop()
    if (retryInterval) clearInterval(retryInterval)
    isRecording.value = false
  }

  onUnmounted(stop)

  return { isRecording, chunkIndex, uploadQueue, start, stop }
}
