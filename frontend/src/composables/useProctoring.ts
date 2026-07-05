import { ref, onUnmounted } from 'vue'
import type { Ref } from 'vue'
import type { ProctoringConfig, ProctoringFlag, ProctoringFlagType } from '@/types/proctoring'
import { proctoringService } from '@/services/proctoring.service'

export function useProctoring(sessionId: Ref<string>, config: Ref<ProctoringConfig | null>) {
  const violations = ref<ProctoringFlag[]>([])
  const violationCount = ref(0)
  const isFullscreen = ref(false)
  const isActive = ref(false)
  const tabSwitchCount = ref(0)

  function reportViolation(type: ProctoringFlagType, description: string, severity: 'low' | 'medium' | 'high' | 'critical' = 'medium') {
    const flag: ProctoringFlag = {
      id: crypto.randomUUID(),
      session_id: sessionId.value,
      type,
      severity,
      description,
      timestamp: new Date().toISOString(),
      reviewed: false
    }
    violations.value.push(flag)
    violationCount.value++

    // Send to backend
    if (sessionId.value) {
      proctoringService.reportFlag(sessionId.value, { type, description, severity, timestamp: flag.timestamp }).catch(() => {})
    }

    // Check auto-submit threshold
    if (config.value?.auto_submit_on_violation && violationCount.value >= (config.value.max_violations_before_auto_submit || 5)) {
      window.dispatchEvent(new CustomEvent('proctoring:auto-submit'))
    }
  }

  // === Full Screen ===
  async function enterFullscreen() {
    try {
      await document.documentElement.requestFullscreen()
      isFullscreen.value = true
    } catch { /* user denied */ }
  }

  function onFullscreenChange() {
    isFullscreen.value = !!document.fullscreenElement
    if (!document.fullscreenElement && isActive.value) {
      reportViolation('fullscreen_exit', 'Exited full screen mode', 'high')
    }
  }

  // === Tab Switch Detection ===
  function onVisibilityChange() {
    if (document.hidden && isActive.value) {
      tabSwitchCount.value++
      const maxAllowed = config.value?.max_tab_switches ?? 0
      const severity = tabSwitchCount.value > maxAllowed ? 'high' : 'medium'
      reportViolation('tab_switch', `Tab switch #${tabSwitchCount.value}`, severity)
    }
  }

  function onWindowBlur() {
    if (isActive.value) {
      reportViolation('window_blur', 'Window lost focus', 'medium')
    }
  }

  // === Copy/Paste Blocking ===
  function onCopy(e: ClipboardEvent) { if (isActive.value && config.value?.block_copy_paste) { e.preventDefault(); reportViolation('copy_paste', 'Copy attempted', 'low') } }
  function onPaste(e: ClipboardEvent) { if (isActive.value && config.value?.block_copy_paste) { e.preventDefault(); reportViolation('copy_paste', 'Paste attempted', 'low') } }
  function onCut(e: ClipboardEvent) { if (isActive.value && config.value?.block_copy_paste) { e.preventDefault() } }
  function onContextMenu(e: MouseEvent) { if (isActive.value && config.value?.block_right_click) { e.preventDefault(); reportViolation('right_click', 'Right-click attempted', 'low') } }

  // === Keyboard Shortcuts ===
  function onKeyDown(e: KeyboardEvent) {
    if (!isActive.value) return
    // Block Ctrl+C/V/U/S, F12, Ctrl+Shift+I/J/C
    if (e.ctrlKey && ['c', 'v', 'u', 's'].includes(e.key.toLowerCase())) { e.preventDefault(); reportViolation('shortcut_blocked', `Ctrl+${e.key} blocked`, 'low') }
    if (e.ctrlKey && e.shiftKey && ['i', 'j', 'c'].includes(e.key.toLowerCase())) { e.preventDefault(); reportViolation('dev_tools', 'DevTools shortcut attempted', 'high') }
    if (e.key === 'F12') { e.preventDefault(); reportViolation('dev_tools', 'F12 blocked', 'high') }
    if (e.key === 'PrintScreen') { e.preventDefault(); reportViolation('screenshot', 'PrintScreen blocked', 'high') }
  }

  // === Start / Stop ===
  function start() {
    isActive.value = true
    document.addEventListener('fullscreenchange', onFullscreenChange)
    document.addEventListener('visibilitychange', onVisibilityChange)
    window.addEventListener('blur', onWindowBlur)
    document.addEventListener('copy', onCopy)
    document.addEventListener('paste', onPaste)
    document.addEventListener('cut', onCut)
    document.addEventListener('contextmenu', onContextMenu)
    document.addEventListener('keydown', onKeyDown)
    if (config.value?.browser_lockdown) enterFullscreen()
  }

  function stop() {
    isActive.value = false
    document.removeEventListener('fullscreenchange', onFullscreenChange)
    document.removeEventListener('visibilitychange', onVisibilityChange)
    window.removeEventListener('blur', onWindowBlur)
    document.removeEventListener('copy', onCopy)
    document.removeEventListener('paste', onPaste)
    document.removeEventListener('cut', onCut)
    document.removeEventListener('contextmenu', onContextMenu)
    document.removeEventListener('keydown', onKeyDown)
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {})
  }

  onUnmounted(stop)

  return { violations, violationCount, isFullscreen, isActive, tabSwitchCount, start, stop, reportViolation, enterFullscreen }
}
