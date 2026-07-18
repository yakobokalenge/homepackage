<script setup lang="ts">
import { computed, watch, ref } from 'vue'
import { Question } from '../../types/assessment'
import katex from 'katex'
import 'katex/dist/katex.min.css'

const props = defineProps<{
  question: Question
  modelValue: {
    selected_options?: string[]
    text_answer?: string
    matching_pairs?: Record<string, string>
    ordering_sequence?: string[]
  }
}>()

const emit = defineEmits(['update:modelValue', 'upload-file'])

// Helper to render LaTeX math blocks and HTML tags
function formatText(text: string): string {
  if (!text) return ''
  
  // Replace block math $$ ... $$
  let parsed = text.replace(/\$\$(.*?)\$\$/gs, (_, math) => {
    try {
      return katex.renderToString(math, { displayMode: true, throwOnError: false })
    } catch {
      return math
    }
  })
  
  // Replace inline math $ ... $
  parsed = parsed.replace(/\$(.*?)\$/g, (_, math) => {
    try {
      return katex.renderToString(math, { displayMode: false, throwOnError: false })
    } catch {
      return math
    }
  })
  
  return parsed
}

// Local models mirroring the modelValue prop
const selectedOptions = ref<string[]>([])
const textAnswer = ref('')
const matchingPairs = ref<Record<string, string>>({})
const orderingSequence = ref<string[]>([])

// Synchronize prop value change to local state
watch(
  () => props.modelValue,
  (newVal) => {
    selectedOptions.value = [...(newVal.selected_options || [])]
    textAnswer.value = newVal.text_answer || ''
    matchingPairs.value = { ...(newVal.matching_pairs || {}) }
    orderingSequence.value = [...(newVal.ordering_sequence || [])]
    
    // Initialize ordering sequence if empty
    if (props.question.question_type === 'ordering' && orderingSequence.value.length === 0) {
      orderingSequence.value = props.question.options.map(o => o.id)
      updateValue()
    }
  },
  { immediate: true, deep: true }
)

function updateValue() {
  emit('update:modelValue', {
    selected_options: selectedOptions.value,
    text_answer: textAnswer.value,
    matching_pairs: matchingPairs.value,
    ordering_sequence: orderingSequence.value
  })
}

// MCQ selection
function selectMCQ(optionId: string) {
  selectedOptions.value = [optionId]
  updateValue()
}

// Multi Select checkbox toggle
function toggleCheckbox(optionId: string) {
  const idx = selectedOptions.value.indexOf(optionId)
  if (idx > -1) {
    selectedOptions.value.splice(idx, 1)
  } else {
    selectedOptions.value.push(optionId)
  }
  updateValue()
}

// Text change
function onTextChange() {
  updateValue()
}

// Matching selections
const matchPool = computed(() => {
  // Get all unique match pairs shuffle them
  return props.question.options
    .map(o => o.match_pair)
    .filter(Boolean)
    .sort(() => Math.random() - 0.5)
})

function setMatch(optionId: string, matchedText: string) {
  matchingPairs.value[optionId] = matchedText
  updateValue()
}

// Ordering sequence movement
function moveOrder(index: number, direction: 'up' | 'down') {
  const targetIdx = direction === 'up' ? index - 1 : index + 1
  if (targetIdx < 0 || targetIdx >= orderingSequence.value.length) return
  
  // Swap items
  const temp = orderingSequence.value[index]
  orderingSequence.value[index] = orderingSequence.value[targetIdx]
  orderingSequence.value[targetIdx] = temp
  updateValue()
}

const orderedOptions = computed(() => {
  return orderingSequence.value.map(id => {
    return props.question.options.find(o => o.id === id)
  }).filter(Boolean) as any[]
})

// File upload handler
function handleFileUpload(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    emit('upload-file', target.files[0])
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Question Text -->
    <div class="prose max-w-none dark:prose-invert text-gray-800 dark:text-gray-200">
      <div v-html="formatText(props.question.text)" class="text-sm md:text-base font-medium leading-relaxed"></div>
      
      <!-- Bilingual translation Kiswahili if available -->
      <div v-if="props.question.text_sw" class="mt-3 p-3 bg-blue-50/50 dark:bg-blue-950/20 border-l-4 border-blue-400 rounded-r-xl">
        <p class="text-[10px] font-bold text-blue-700 dark:text-blue-400 uppercase tracking-wider mb-1">Kiswahili translation</p>
        <div v-html="formatText(props.question.text_sw)" class="text-xs md:text-sm text-gray-600 dark:text-gray-400 italic"></div>
      </div>
    </div>

    <!-- Media uploads display if any -->
    <div v-if="props.question.media && props.question.media.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div v-for="mediaUrl in props.question.media" :key="mediaUrl" class="overflow-hidden rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm">
        <img :src="mediaUrl" alt="Illustration" class="w-full object-cover max-h-72" />
      </div>
    </div>

    <!-- Input Types Render -->
    <div class="mt-6">
      
      <!-- MCQ & TRUE FALSE -->
      <div v-if="props.question.question_type === 'mcq' || props.question.question_type === 'true_false'" class="space-y-3">
        <button
          v-for="opt in props.question.options"
          :key="opt.id"
          @click="selectMCQ(opt.id)"
          :class="[
            selectedOptions.includes(opt.id)
              ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-950/30 text-blue-800 dark:text-blue-300 ring-2 ring-blue-400'
              : 'border-gray-200 dark:border-gray-800 hover:border-gray-300 hover:bg-gray-50 dark:hover:bg-gray-900',
            'w-full text-left p-4 rounded-xl border flex items-center justify-between transition-all duration-200 group'
          ]"
        >
          <div class="flex items-center gap-3">
            <span :class="[
              selectedOptions.includes(opt.id)
                ? 'bg-blue-600 border-blue-600 text-white'
                : 'border-gray-300 dark:border-gray-700 text-transparent',
              'w-5 h-5 rounded-full border flex items-center justify-center text-xs font-bold'
            ]">
              ✓
            </span>
            <div v-html="formatText(opt.text)" class="text-xs md:text-sm"></div>
          </div>
        </button>
      </div>

      <!-- MULTIPLE SELECT -->
      <div v-else-if="props.question.question_type === 'multi_select'" class="space-y-3">
        <button
          v-for="opt in props.question.options"
          :key="opt.id"
          @click="toggleCheckbox(opt.id)"
          :class="[
            selectedOptions.includes(opt.id)
              ? 'border-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/30 text-emerald-800 dark:text-emerald-300 ring-2 ring-emerald-400'
              : 'border-gray-200 dark:border-gray-800 hover:border-gray-300 hover:bg-gray-50 dark:hover:bg-gray-900',
            'w-full text-left p-4 rounded-xl border flex items-center justify-between transition-all duration-200 group'
          ]"
        >
          <div class="flex items-center gap-3">
            <span :class="[
              selectedOptions.includes(opt.id)
                ? 'bg-emerald-600 border-emerald-600 text-white'
                : 'border-gray-300 dark:border-gray-700 text-transparent',
              'w-5 h-5 rounded border flex items-center justify-center text-xs font-bold'
            ]">
              ✓
            </span>
            <div v-html="formatText(opt.text)" class="text-xs md:text-sm"></div>
          </div>
        </button>
      </div>

      <!-- FILL IN THE BLANK / SHORT ANSWER -->
      <div v-else-if="props.question.question_type === 'fill_blank' || props.question.question_type === 'short_answer'" class="space-y-2">
        <label class="block text-xs font-bold text-gray-500 uppercase">Write your answer below</label>
        <input
          type="text"
          v-model="textAnswer"
          @input="onTextChange"
          placeholder="Type answer here..."
          class="w-full px-4 py-3 border border-gray-200 dark:border-gray-800 rounded-xl bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all text-sm"
        />
      </div>

      <!-- ESSAY -->
      <div v-else-if="props.question.question_type === 'essay'" class="space-y-4">
        <div class="space-y-2">
          <label class="block text-xs font-bold text-gray-500 uppercase">Write your essay response</label>
          <textarea
            rows="6"
            v-model="textAnswer"
            @input="onTextChange"
            placeholder="Type your essay details..."
            class="w-full px-4 py-3 border border-gray-200 dark:border-gray-800 rounded-xl bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all text-sm leading-relaxed"
          ></textarea>
        </div>

        <!-- Handwritten attachment option -->
        <div class="p-4 bg-gray-50 dark:bg-gray-900 border border-dashed border-gray-300 dark:border-gray-800 rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-4">
          <div class="text-center sm:text-left">
            <p class="text-xs font-bold text-gray-700 dark:text-gray-300">Upload Handwritten PDF or Image</p>
            <p class="text-[10px] text-gray-500 mt-0.5">If you solved this question on a physical paper, capture and upload it.</p>
          </div>
          <label class="flex-shrink-0 cursor-pointer px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 text-xs font-bold rounded-xl shadow-sm hover:bg-gray-50 transition-all text-gray-700 dark:text-gray-300">
            <span>📎 Select File</span>
            <input type="file" @change="handleFileUpload" class="hidden" accept="image/*,application/pdf" />
          </label>
        </div>
      </div>

      <!-- MATCHING TYPE -->
      <div v-else-if="props.question.question_type === 'matching'" class="space-y-3">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 items-center" v-for="opt in props.question.options" :key="opt.id">
          <div class="p-3 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl text-xs md:text-sm font-medium" v-html="formatText(opt.text)"></div>
          <div>
            <select
              :value="matchingPairs[opt.id] || ''"
              @change="setMatch(opt.id, ($event.target as HTMLSelectElement).value)"
              class="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:outline-none text-xs md:text-sm"
            >
              <option value="">-- Choose Match --</option>
              <option v-for="pairText in matchPool" :key="pairText" :value="pairText">{{ pairText }}</option>
            </select>
          </div>
        </div>
      </div>

      <!-- ORDERING TYPE -->
      <div v-else-if="props.question.question_type === 'ordering'" class="space-y-2">
        <p class="text-xs text-gray-500 mb-2">Arrange the items below in the correct sequence order:</p>
        <div
          v-for="(opt, idx) in orderedOptions"
          :key="opt.id"
          class="p-4 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl flex items-center justify-between gap-3 shadow-sm hover:shadow-md transition-shadow"
        >
          <div class="flex items-center gap-3">
            <span class="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-400 flex items-center justify-center text-xs font-bold">{{ idx + 1 }}</span>
            <div v-html="formatText(opt.text)" class="text-xs md:text-sm"></div>
          </div>
          <div class="flex items-center gap-1.5">
            <button
              @click="moveOrder(idx, 'up')"
              :disabled="idx === 0"
              class="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-800 rounded-lg text-gray-500 disabled:opacity-30"
              title="Move Up"
            >
              ▲
            </button>
            <button
              @click="moveOrder(idx, 'down')"
              :disabled="idx === orderedOptions.length - 1"
              class="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-800 rounded-lg text-gray-500 disabled:opacity-30"
              title="Move Down"
            >
              ▼
            </button>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>
