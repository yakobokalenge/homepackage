<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { proctoringService } from '../../services/proctoring.service'
import { ProctoringSession } from '../../types/proctoring'
import { useNotificationStore } from '../../stores/notification'

const route = useRoute()
const router = useRouter()
const notificationStore = useNotificationStore()

const attemptId = route.params.attemptId as string
const session = ref<ProctoringSession | null>(null)
const loading = ref(true)
const saving = ref(false)
const reviewNotes = ref('')
const selectedVideoChunk = ref('')

async function loadSession() {
  loading.value = true
  try {
    // Proctoring sessions query can use attempt ID to filter or search
    const sessions = await proctoringService.getSessions({ attempt: attemptId })
    if (sessions.length > 0) {
      // Load details of the first matching session
      session.value = await proctoringService.getSession(sessions[0].id)
      reviewNotes.value = session.value.teacher_review_notes || ''
      if (session.value.recording_urls.length > 0) {
        selectedVideoChunk.value = session.value.recording_urls[0]
      }
    } else {
      notificationStore.warning('No proctoring session found for this attempt.')
    }
  } catch {
    notificationStore.error('Failed to load proctoring session details.')
  } finally {
    loading.value = false
  }
}

async function handleSaveReview() {
  if (!session.value) return
  saving.value = true
  try {
    await proctoringService.submitReview(session.value.id, reviewNotes.value)
    notificationStore.success('Proctoring review finalized.')
    router.back()
  } catch {
    notificationStore.error('Failed to submit proctoring review.')
  } finally {
    saving.value = false
  }
}

onMounted(loadSession)
</script>

<template>
  <div class="space-y-6 max-w-5xl mx-auto">
    <!-- Back Button -->
    <button @click="router.back()" class="text-xs font-bold text-blue-600 hover:text-blue-800">
      ◀ Back
    </button>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
      <span class="animate-spin inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mb-4"></span>
      <p class="text-gray-500">Loading Proctoring Session...</p>
    </div>

    <!-- Main review workspace -->
    <template v-else-if="session">
      <!-- Session Header -->
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 class="text-lg font-bold text-gray-900 dark:text-white">Proctoring Review Workspace</h1>
          <p class="text-xs text-gray-500 mt-1">Student: <span class="font-bold text-gray-900 dark:text-white">{{ session.student_name }}</span> · Assessment: {{ session.assessment_title }}</p>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs font-bold text-gray-550 uppercase">Suspicion Index:</span>
          <span :class="[
            parseFloat(session.suspicion_score) > 50 ? 'bg-red-50 text-red-700 border-red-200' :
            parseFloat(session.suspicion_score) > 20 ? 'bg-amber-50 text-amber-700 border-amber-200' :
            'bg-emerald-50 text-emerald-700 border-emerald-200',
            'px-2 py-1 rounded-xl text-xs font-bold border'
          ]">
            {{ session.suspicion_score }}%
          </span>
        </div>
      </div>

      <!-- Playback grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Video playback -->
        <div class="lg:col-span-2 space-y-4">
          <div class="bg-black aspect-video rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden flex items-center justify-center relative">
            <video
              v-if="selectedVideoChunk"
              controls
              :src="selectedVideoChunk"
              class="w-full h-full object-contain"
            ></video>
            <div v-else class="text-center p-6 text-gray-500">
              <span class="text-3xl block">🎥</span>
              <span class="text-xs">No video recording logs available.</span>
            </div>
          </div>

          <!-- Video chunk selection list -->
          <div v-if="session.recording_urls.length > 1" class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-4 space-y-3">
            <label class="text-[10px] font-bold text-gray-550 uppercase">Select Video Chunk Segment</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="(url, idx) in session.recording_urls"
                :key="url"
                @click="selectedVideoChunk = url"
                :class="[
                  selectedVideoChunk === url
                    ? 'bg-blue-600 border-blue-600 text-white'
                    : 'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300',
                  'px-3 py-1.5 text-xs font-bold border rounded-lg shadow-sm transition-all'
                ]"
              >
                Segment {{ idx + 1 }}
              </button>
            </div>
          </div>

          <!-- Review form -->
          <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 space-y-4">
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Teacher Proctoring Review Comments</label>
              <textarea rows="3" v-model="reviewNotes" placeholder="Write logs, warnings, or audit findings..." class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none"></textarea>
            </div>
            <button
              @click="handleSaveReview"
              :disabled="saving"
              class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-md flex items-center justify-center gap-2"
            >
              <span v-if="saving" class="animate-spin inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full"></span>
              Submit Review Verdict
            </button>
          </div>
        </div>

        <!-- Suspicion Flags log list -->
        <div class="space-y-4">
          <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 space-y-4 max-h-[500px] overflow-y-auto pr-1">
            <h2 class="text-sm font-bold text-gray-900 dark:text-white">Flagged Incidents Log ({{ session.flags?.length || 0 }})</h2>
            
            <div v-if="!session.flags || session.flags.length === 0" class="text-center py-10 text-gray-500">
              <span class="text-3xl block">🛡️</span>
              <span class="text-xs">No proctoring violations flagged.</span>
            </div>

            <div v-else class="space-y-4">
              <div
                v-for="flag in session.flags"
                :key="flag.id"
                class="p-3 bg-gray-50 dark:bg-gray-950 border border-gray-250 dark:border-gray-850 rounded-2xl space-y-2 relative"
              >
                <!-- Badge header -->
                <div class="flex items-center justify-between">
                  <span class="px-1.5 py-0.5 bg-red-100 text-red-700 text-[8px] font-bold rounded uppercase">
                    {{ flag.flag_type.replace('_', ' ') }}
                  </span>
                  <span class="text-[9px] font-mono text-gray-500 font-bold">Offset: {{ Math.floor(flag.timestamp / 60) }}m {{ flag.timestamp % 60 }}s</span>
                </div>
                
                <p class="text-[11px] text-gray-600 dark:text-gray-400 mt-1">{{ flag.description }}</p>
                
                <!-- Violation Screenshot display -->
                <div v-if="flag.screenshot" class="mt-2 rounded-lg border overflow-hidden">
                  <img :src="flag.screenshot" alt="Incident Screenshot" class="w-full object-cover max-h-32" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
