import { ref } from 'vue'

export function useVideoRecorder() {
  const stream = ref<MediaStream | null>(null)
  const isRecording = ref(false)
  let mediaRecorder: MediaRecorder | null = null
  let recordedChunks: Blob[] = []
  let chunkUploadInterval: any = null
  
  // Captures photo from stream and returns Blob
  function capturePhoto(videoElement: HTMLVideoElement): Promise<Blob> {
    return new Promise((resolve, reject) => {
      try {
        const canvas = document.createElement('canvas')
        canvas.width = videoElement.videoWidth || 640
        canvas.height = videoElement.videoHeight || 480
        const ctx = canvas.getContext('2d')
        if (ctx) {
          ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height)
          canvas.toBlob((blob) => {
            if (blob) {
              resolve(blob)
            } else {
              reject(new Error('Failed to convert canvas to blob'))
            }
          }, 'image/jpeg', 0.95)
        } else {
          reject(new Error('Could not get canvas context'))
        }
      } catch (err) {
        reject(err)
      }
    })
  }

  async function startCamera(requireAudio = true): Promise<MediaStream> {
    try {
      const constraints: MediaStreamConstraints = {
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        },
        audio: requireAudio
      }
      const mediaStream = await navigator.mediaDevices.getUserMedia(constraints)
      stream.value = mediaStream
      return mediaStream
    } catch (err) {
      console.error('Camera stream access failed:', err)
      throw err
    }
  }

  function stopCamera() {
    stopRecording()
    if (stream.value) {
      stream.value.getTracks().forEach((track) => track.stop())
      stream.value = null
    }
  }

  // Records webcam video in chunks and calls callback to upload each chunk
  function startRecording(onChunkReady: (blob: Blob) => void, chunkIntervalMs = 15000) {
    if (!stream.value || isRecording.value) return

    recordedChunks = []
    
    // Choose appropriate mime type
    const options = { mimeType: 'video/webm;codecs=vp8,opus' }
    try {
      mediaRecorder = new MediaRecorder(stream.value, options)
    } catch (e) {
      try {
        mediaRecorder = new MediaRecorder(stream.value, { mimeType: 'video/webm' })
      } catch (err) {
        mediaRecorder = new MediaRecorder(stream.value)
      }
    }

    mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        onChunkReady(event.data)
      }
    }

    // Start recording, triggers ondataavailable every chunkIntervalMs
    mediaRecorder.start(chunkIntervalMs)
    isRecording.value = true
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop()
      mediaRecorder = null
    }
    isRecording.value = false
  }

  return {
    stream,
    isRecording,
    startCamera,
    stopCamera,
    capturePhoto,
    startRecording,
    stopRecording
  }
}
