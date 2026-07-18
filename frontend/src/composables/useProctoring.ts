import { ref, onUnmounted } from 'vue'
import { useBrowserLockdown } from './useBrowserLockdown'
import { useVideoRecorder } from './useVideoRecorder'
import { useFaceDetection } from './useFaceDetection'
import { useAudioMonitor } from './useAudioMonitor'
import { proctoringService } from '../services/proctoring.service'
import { ProctoringConfig } from '../types/proctoring'
import { useExamStore } from '../stores/exam'

export function useProctoring() {
  const isStarted = ref(false)
  const isCameraActive = ref(false)
  
  // Composables
  const lockdown = useBrowserLockdown()
  const recorder = useVideoRecorder()
  const faceDetector = useFaceDetection()
  const audioMonitor = useAudioMonitor()
  
  const examStore = useExamStore()

  // Track violations locally to prevent spamming reports
  const lastReportedViolation = ref<Record<string, number>>({})
  const REPORT_COOLDOWN_MS = 5000 // 5 seconds between same flag reports

  async function startProctoring(
    sessionId: string,
    config: ProctoringConfig,
    videoElement: HTMLVideoElement
  ) {
    if (isStarted.value) return
    isStarted.value = true

    // Define standard violation reporter
    async function reportViolation(type: string, description: string, severity: string) {
      const now = Date.now()
      const lastTime = lastReportedViolation.value[type] || 0
      if (now - lastTime < REPORT_COOLDOWN_MS) return
      
      lastReportedViolation.value[type] = now

      // Capture screenshot if camera is running
      let screenshotBlob: Blob | null = null
      if (config.require_webcam && videoElement) {
        try {
          screenshotBlob = await recorder.capturePhoto(videoElement)
        } catch (e) {
          console.warn('Screenshot capture failed:', e)
        }
      }

      // Calculate time offset in seconds since exam started
      let timestamp = 0
      if (examStore.currentAttempt?.started_at) {
        const start = new Date(examStore.currentAttempt.started_at).getTime()
        timestamp = Math.max(0, Math.floor((now - start) / 1000))
      }

      try {
        const res = await proctoringService.reportFlag(sessionId, {
          flag_type: type as any,
          severity: severity as any,
          timestamp,
          description,
          screenshot: screenshotBlob,
          metadata: {
            tabSwitches: lockdown.tabSwitchesCount.value,
            isFullscreen: lockdown.isFullscreen.value
          }
        })
        
        // Handle termination if attempt is auto-submitted on violation count
        if (res.terminated) {
          stopProctoring()
          alert('This assessment attempt has been terminated due to too many proctoring violations.')
          window.location.reload()
        }
      } catch (err) {
        console.error('Failed to report violation flag:', err)
      }
    }

    // 1. Browser Lockdown
    if (config.require_fullscreen) {
      lockdown.start(reportViolation)
    }

    // 2. Video Recorder
    if (config.require_webcam) {
      try {
        const stream = await recorder.startCamera(config.require_microphone)
        videoElement.srcObject = stream
        videoElement.play()
        isCameraActive.value = true

        // AI Face tracking
        if (config.ai_monitoring_enabled) {
          await faceDetector.initialize()
          faceDetector.startProcessingLoop(videoElement, reportViolation)
        }

        // Recording
        if (config.record_video) {
          recorder.startRecording(async (chunkBlob) => {
            try {
              await proctoringService.uploadRecordingChunk(sessionId, chunkBlob)
            } catch (err) {
              console.error('Failed to upload recording chunk:', err)
            }
          }, 15000) // upload every 15s
        }

        // Voice VAD monitor
        if (config.require_microphone && config.ai_monitoring_enabled) {
          audioMonitor.start(stream, reportViolation)
        }
      } catch (err) {
        console.error('Camera startup failed:', err)
        reportViolation('other', 'Webcam / camera device permission failed or blocked.', 'high')
      }
    }
  }

  function stopProctoring() {
    if (!isStarted.value) return
    isStarted.value = false
    isCameraActive.value = false

    lockdown.stop()
    recorder.stopRecording()
    recorder.stopCamera()
    faceDetector.cleanup()
    audioMonitor.stop()
  }

  onUnmounted(stopProctoring)

  return {
    isStarted,
    isCameraActive,
    lockdown,
    recorder,
    faceDetector,
    audioMonitor,
    startProctoring,
    stopProctoring
  }
}
