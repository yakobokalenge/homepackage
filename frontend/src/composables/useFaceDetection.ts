import { ref, onUnmounted } from 'vue'

export function useFaceDetection() {
  const faceCount = ref(0)
  const isLookingAway = ref(false)
  const headPose = ref<{ yaw: number; pitch: number; roll: number } | null>(null)
  const isInitialized = ref(false)
  const isProcessing = ref(false)
  let faceDetector: any = null
  let faceLandmarker: any = null
  let animationFrameId: number | null = null
  let lastProcessTime = 0
  const PROCESS_INTERVAL = 500 // Process every 500ms to save CPU

  async function initialize() {
    try {
      const { FaceDetector, FaceLandmarker, FilesetResolver } = await import('@mediapipe/tasks-vision')
      const vision = await FilesetResolver.forVisionTasks(
        'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision/wasm'
      )
      faceDetector = await FaceDetector.createFromOptions(vision, {
        baseOptions: {
          modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite',
          delegate: 'GPU'
        },
        runningMode: 'VIDEO',
        minDetectionConfidence: 0.5
      })
      faceLandmarker = await FaceLandmarker.createFromOptions(vision, {
        baseOptions: {
          modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
          delegate: 'GPU'
        },
        runningMode: 'VIDEO',
        numFaces: 2,
        outputFacialTransformationMatrixes: true
      })
      isInitialized.value = true
    } catch (err) {
      console.error('Face detection initialization failed:', err)
    }
  }

  function processFrame(videoElement: HTMLVideoElement, onViolation: (type: string, desc: string, severity: string) => void) {
    if (!isInitialized.value || !faceDetector || isProcessing.value) return

    const now = performance.now()
    if (now - lastProcessTime < PROCESS_INTERVAL) return
    lastProcessTime = now
    isProcessing.value = true

    try {
      // Face detection
      const detections = faceDetector.detectForVideo(videoElement, now)
      faceCount.value = detections.detections.length

      if (faceCount.value === 0) {
        onViolation('no_face', 'No face detected in frame', 'high')
      } else if (faceCount.value > 1) {
        onViolation('multiple_faces', `${faceCount.value} faces detected`, 'high')
      }

      // Head pose via landmarks
      if (faceLandmarker) {
        const landmarkResult = faceLandmarker.detectForVideo(videoElement, now)
        if (landmarkResult.facialTransformationMatrixes?.length > 0) {
          const matrix = landmarkResult.facialTransformationMatrixes[0].data
          const yaw = Math.atan2(matrix[8], matrix[0]) * (180 / Math.PI)
          const pitch = Math.atan2(-matrix[4], Math.sqrt(matrix[5] ** 2 + matrix[6] ** 2)) * (180 / Math.PI)
          const roll = Math.atan2(matrix[5], matrix[6]) * (180 / Math.PI)
          headPose.value = { yaw, pitch, roll }

          const YAW_THRESHOLD = 30
          const PITCH_THRESHOLD = 25
          isLookingAway.value = Math.abs(yaw) > YAW_THRESHOLD || Math.abs(pitch) > PITCH_THRESHOLD

          if (isLookingAway.value) {
            onViolation('looking_away', `Head turned: yaw=${yaw.toFixed(1)}°, pitch=${pitch.toFixed(1)}°`, 'medium')
          }
        }
      }
    } catch { /* skip frame on error */ }
    finally {
      isProcessing.value = false
    }
  }

  function startProcessingLoop(videoElement: HTMLVideoElement, onViolation: (type: string, desc: string, severity: string) => void) {
    function loop() {
      processFrame(videoElement, onViolation)
      animationFrameId = requestAnimationFrame(loop)
    }
    loop()
  }

  function stopProcessingLoop() {
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId)
      animationFrameId = null
    }
  }

  function cleanup() {
    stopProcessingLoop()
    faceDetector?.close()
    faceLandmarker?.close()
    faceDetector = null
    faceLandmarker = null
    isInitialized.value = false
  }

  onUnmounted(cleanup)

  return { faceCount, isLookingAway, headPose, isInitialized, initialize, startProcessingLoop, stopProcessingLoop, cleanup }
}
