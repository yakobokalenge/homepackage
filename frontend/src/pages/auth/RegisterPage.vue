<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import api from '@/services/api'

const { t } = useI18n()
const router = useRouter()
const auth = useAuthStore()

const form = ref({
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  password: '',
  confirm_password: '',
  role: 'student' as 'student' | 'teacher',
  region: '',
  school: '',
  classroom: ''
})

// Database lists
const schools = ref<any[]>([])
const classrooms = ref<any[]>([])

const regions = [
  "Arusha", "Dar es Salaam", "Dodoma", "Geita", "Iringa", "Kagera",
  "Katavi", "Kigoma", "Kilimanjaro", "Lindi", "Manyara", "Mara",
  "Mbeya", "Morogoro", "Mtwara", "Mwanza", "Njombe", "Pemba North",
  "Pemba South", "Pwani (Coast)", "Rukwa", "Ruvuma", "Shinyanga",
  "Simiyu", "Singida", "Songwe", "Tabora", "Tanga",
  "Zanzibar Central/South", "Zanzibar North", "Zanzibar Urban/West"
]

// Dropdown UI flags
const regionOpen = ref(false)
const schoolOpen = ref(false)
const classOpen = ref(false)

const regionSearch = ref('')
const schoolSearch = ref('')
const classSearch = ref('')

// Computed search filters
const filteredRegions = computed(() => {
  if (!regionSearch.value || regionSearch.value === form.value.region) return regions
  return regions.filter(r => r.toLowerCase().includes(regionSearch.value.toLowerCase()))
})

const filteredSchools = computed(() => {
  const selectedSchoolObj = schools.value.find(s => s.id === form.value.school)
  if (!schoolSearch.value || (selectedSchoolObj && schoolSearch.value === selectedSchoolObj.name)) return schools.value
  return schools.value.filter(s => s.name.toLowerCase().includes(schoolSearch.value.toLowerCase()))
})

const filteredClassrooms = computed(() => {
  const selectedClassroomObj = classrooms.value.find(c => c.id === form.value.classroom)
  if (!classSearch.value || (selectedClassroomObj && classSearch.value === selectedClassroomObj.name)) return classrooms.value
  return classrooms.value.filter(c => c.name.toLowerCase().includes(classSearch.value.toLowerCase()))
})

// Blur reset handlers to manage selection states
function handleRegionBlur() {
  setTimeout(() => {
    regionOpen.value = false
    regionSearch.value = form.value.region || ''
  }, 200)
}

function handleSchoolBlur() {
  setTimeout(() => {
    schoolOpen.value = false
    const selectedSchoolObj = schools.value.find(s => s.id === form.value.school)
    schoolSearch.value = selectedSchoolObj ? selectedSchoolObj.name : ''
  }, 200)
}

function handleClassBlur() {
  setTimeout(() => {
    classOpen.value = false
    const selectedClassroomObj = classrooms.value.find(c => c.id === form.value.classroom)
    classSearch.value = selectedClassroomObj ? selectedClassroomObj.name : ''
  }, 200)
}

// Search selections
async function selectRegion(region: string) {
  regionSearch.value = region
  form.value.region = region
  regionOpen.value = false
  
  // reset downstreams
  form.value.school = ''
  schoolSearch.value = ''
  schools.value = []
  
  form.value.classroom = ''
  classSearch.value = ''
  classrooms.value = []

  try {
    const { data } = await api.get('/schools/schools/', { params: { region, limit: 100 } })
    schools.value = data.results || data || []
  } catch (err) {
    console.error('Failed to load schools:', err)
  }
}

async function selectSchool(school: any) {
  schoolSearch.value = school.name
  form.value.school = school.id
  schoolOpen.value = false
  
  // reset downstreams
  form.value.classroom = ''
  classSearch.value = ''
  classrooms.value = []

  try {
    const { data } = await api.get('/schools/classrooms/', { params: { school: school.id, limit: 100 } })
    const list = data.results || data || []
    const seen = new Set()
    classrooms.value = list.filter((item: any) => {
      const key = `${item.name}-${item.stream}`
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
  } catch (err) {
    console.error('Failed to load classrooms:', err)
  }
}

function selectClass(classroom: any) {
  classSearch.value = classroom.name
  form.value.classroom = classroom.id
  classOpen.value = false
}

async function handleRegister() {
  if (form.value.password !== form.value.confirm_password) {
    auth.error = 'Passwords do not match'
    return
  }
  
  if (!form.value.school || !form.value.classroom) {
    auth.error = 'Please select your region, school and classroom.'
    return
  }

  auth.clearError()
  try {
    await auth.register({
      email: form.value.email,
      password: form.value.password,
      password_confirm: form.value.confirm_password,
      first_name: form.value.first_name,
      last_name: form.value.last_name,
      phone: form.value.phone,
      role: form.value.role,
      school: form.value.school || undefined,
      classroom: form.value.classroom || undefined,
    })
    router.push(form.value.role === 'teacher' ? '/teacher/dashboard' : '/student/dashboard')
  } catch { /* error handled in store */ }
}
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold text-white text-center mb-2">{{ t('auth.register_title') }}</h2>
    <p class="text-blue-200 text-sm text-center mb-8">{{ t('auth.register_subtitle') }}</p>

    <form @submit.prevent="handleRegister" class="space-y-4">
      <!-- Role Selection -->
      <div>
        <label class="block text-xs font-medium text-blue-100 mb-2">{{ t('auth.role') }}</label>
        <div class="grid grid-cols-2 gap-3">
          <button type="button" @click="form.role = 'student'"
            :class="['p-3 rounded-xl border text-center transition-all', form.role === 'student' ? 'bg-amber-500/20 border-amber-400 text-amber-300' : 'bg-white/5 border-white/20 text-white hover:bg-white/10']">
            <span class="text-xl block mb-0.5">🎓</span>
            <span class="text-sm font-medium">{{ t('auth.student') }}</span>
          </button>
          <button type="button" @click="form.role = 'teacher'"
            :class="['p-3 rounded-xl border text-center transition-all', form.role === 'teacher' ? 'bg-amber-500/20 border-amber-400 text-amber-300' : 'bg-white/5 border-white/20 text-white hover:bg-white/10']">
            <span class="text-xl block mb-0.5">👩‍🏫</span>
            <span class="text-sm font-medium">{{ t('auth.teacher') }}</span>
          </button>
        </div>
      </div>

      <!-- Names -->
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-blue-100 mb-1">{{ t('auth.first_name') }}</label>
          <input v-model="form.first_name" required class="w-full px-3 py-2 rounded-xl bg-white/10 border border-white/20 text-white placeholder-blue-300/50 focus:ring-2 focus:ring-amber-400 focus:outline-none text-sm" />
        </div>
        <div>
          <label class="block text-xs font-medium text-blue-100 mb-1">{{ t('auth.last_name') }}</label>
          <input v-model="form.last_name" required class="w-full px-3 py-2 rounded-xl bg-white/10 border border-white/20 text-white placeholder-blue-300/50 focus:ring-2 focus:ring-amber-400 focus:outline-none text-sm" />
        </div>
      </div>

      <!-- Email & Phone -->
      <div>
        <label class="block text-xs font-medium text-blue-100 mb-1">{{ t('auth.email') }}</label>
        <input v-model="form.email" type="email" required class="w-full px-3 py-2 rounded-xl bg-white/10 border border-white/20 text-white placeholder-blue-300/50 focus:ring-2 focus:ring-amber-400 focus:outline-none text-sm" />
      </div>
      <div>
        <label class="block text-xs font-medium text-blue-100 mb-1">{{ t('auth.phone') }}</label>
        <input v-model="form.phone" type="tel" placeholder="+255 7XX XXX XXX" class="w-full px-3 py-2 rounded-xl bg-white/10 border border-white/20 text-white placeholder-blue-300/50 focus:ring-2 focus:ring-amber-400 focus:outline-none text-sm" />
      </div>

      <!-- Passwords -->
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-blue-100 mb-1">{{ t('auth.password') }}</label>
          <input v-model="form.password" type="password" required class="w-full px-3 py-2 rounded-xl bg-white/10 border border-white/20 text-white placeholder-blue-300/50 focus:ring-2 focus:ring-amber-400 focus:outline-none text-sm" />
        </div>
        <div>
          <label class="block text-xs font-medium text-blue-100 mb-1">{{ t('auth.confirm_password') }}</label>
          <input v-model="form.confirm_password" type="password" required class="w-full px-3 py-2 rounded-xl bg-white/10 border border-white/20 text-white placeholder-blue-300/50 focus:ring-2 focus:ring-amber-400 focus:outline-none text-sm" />
        </div>
      </div>

      <!-- School & Location Fields -->
      <div class="space-y-4 pt-2 border-t border-white/10">
        <p class="text-xs font-bold text-amber-300 uppercase tracking-wider">School & Location</p>
        
        <!-- Region Dropdown -->
        <div class="relative">
          <label class="block text-xs font-medium text-blue-100 mb-1">Region</label>
          <input
            v-model="regionSearch"
            @focus="regionOpen = true"
            @blur="handleRegionBlur"
            placeholder="Type or select region..."
            class="w-full px-3 py-2 rounded-xl bg-white/10 border border-white/20 text-white placeholder-blue-300/50 focus:ring-2 focus:ring-amber-400 focus:outline-none text-sm"
          />
          <div v-if="regionOpen && filteredRegions.length > 0" class="absolute z-50 w-full mt-1 max-h-48 overflow-y-auto bg-gray-900 border border-white/20 rounded-xl shadow-lg">
            <button
              v-for="r in filteredRegions"
              :key="r"
              type="button"
              @mousedown.prevent="selectRegion(r)"
              class="w-full px-4 py-2 text-left text-sm text-white hover:bg-white/10 transition-colors"
            >
              {{ r }}
            </button>
          </div>
        </div>

        <!-- School Dropdown -->
        <div class="relative">
          <label class="block text-xs font-medium text-blue-100 mb-1">School Name</label>
          <input
            v-model="schoolSearch"
            @focus="schoolOpen = true"
            @blur="handleSchoolBlur"
            :disabled="!form.region"
            placeholder="Select school (Choose region first)..."
            class="w-full px-3 py-2 rounded-xl bg-white/10 border border-white/20 text-white placeholder-blue-300/50 focus:ring-2 focus:ring-amber-400 focus:outline-none text-sm disabled:opacity-50"
          />
          <div v-if="schoolOpen && filteredSchools.length > 0" class="absolute z-50 w-full mt-1 max-h-48 overflow-y-auto bg-gray-900 border border-white/20 rounded-xl shadow-lg">
            <button
              v-for="s in filteredSchools"
              :key="s.id"
              type="button"
              @mousedown.prevent="selectSchool(s)"
              class="w-full px-4 py-2 text-left text-sm text-white hover:bg-white/10 transition-colors"
            >
              {{ s.name }}
            </button>
          </div>
        </div>

        <!-- Class/Classroom Dropdown -->
        <div class="relative">
          <label class="block text-xs font-medium text-blue-100 mb-1">Class / Grade</label>
          <input
            v-model="classSearch"
            @focus="classOpen = true"
            @blur="handleClassBlur"
            :disabled="!form.school"
            placeholder="Select grade / stream..."
            class="w-full px-3 py-2 rounded-xl bg-white/10 border border-white/20 text-white placeholder-blue-300/50 focus:ring-2 focus:ring-amber-400 focus:outline-none text-sm disabled:opacity-50"
          />
          <div v-if="classOpen && filteredClassrooms.length > 0" class="absolute z-50 w-full mt-1 max-h-48 overflow-y-auto bg-gray-900 border border-white/20 rounded-xl shadow-lg">
            <button
              v-for="c in filteredClassrooms"
              :key="c.id"
              type="button"
              @mousedown.prevent="selectClass(c)"
              class="w-full px-4 py-2 text-left text-sm text-white hover:bg-white/10 transition-colors"
            >
              {{ c.name }}
            </button>
          </div>
        </div>
      </div>

      <!-- Error -->
      <div v-if="auth.error" class="p-3 rounded-xl bg-red-500/20 border border-red-400/30 text-red-200 text-sm">{{ auth.error }}</div>

      <!-- Submit -->
      <button type="submit" :disabled="auth.loading" class="w-full py-3 bg-gradient-to-r from-amber-500 to-amber-600 text-white font-semibold rounded-xl hover:shadow-lg disabled:opacity-60 transition-all">
        {{ auth.loading ? t('common.loading') : t('auth.register_btn') }}
      </button>
    </form>

    <p class="text-center text-sm text-blue-200 mt-6">
      {{ t('auth.has_account') }}
      <RouterLink to="/auth/login" class="font-semibold text-amber-300 hover:text-amber-400 ml-1">{{ t('auth.login_btn') }}</RouterLink>
    </p>
  </div>
</template>
