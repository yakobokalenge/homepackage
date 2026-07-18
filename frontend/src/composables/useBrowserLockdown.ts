import { ref, onUnmounted } from 'vue'

export function useBrowserLockdown() {
  const isFullscreen = ref(false)
  const tabSwitchesCount = ref(0)
  const isActive = ref(false)
  let onViolationCallback: (type: string, desc: string, severity: string) => void = () => {}

  function enforceFullscreen() {
    const el = document.documentElement
    if (!document.fullscreenElement) {
      el.requestFullscreen().catch((err) => {
        console.warn('Failed to enter fullscreen:', err)
      })
    }
  }

  function handleFullscreenChange() {
    if (!document.fullscreenElement && isActive.value) {
      isFullscreen.value = false
      onViolationCallback('fullscreen_exit', 'Student exited fullscreen mode', 'medium')
    } else {
      isFullscreen.value = true
    }
  }

  function handleVisibilityChange() {
    if (document.hidden && isActive.value) {
      tabSwitchesCount.value++
      onViolationCallback('tab_switch', `Student switched tab/window (Count: ${tabSwitchesCount.value})`, 'high')
    }
  }

  function handleWindowBlur() {
    if (isActive.value) {
      onViolationCallback('tab_switch', 'Focus lost: window blurred', 'medium')
    }
  }

  function preventCopyPaste(e: ClipboardEvent) {
    if (isActive.value) {
      e.preventDefault()
      onViolationCallback('copy_paste', 'Blocked clipboard operation (copy/paste)', 'low')
    }
  }

  function preventContextMenu(e: MouseEvent) {
    if (isActive.value) {
      e.preventDefault()
      onViolationCallback('right_click', 'Blocked mouse right-click context menu', 'low')
    }
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (!isActive.value) return

    // F12 key
    if (e.key === 'F12') {
      e.preventDefault()
      onViolationCallback('devtools', 'Blocked Developer Tools key (F12)', 'high')
    }

    // Ctrl+Shift+I, Ctrl+Shift+J, Ctrl+Shift+C, Ctrl+U
    if (
      (e.ctrlKey && e.shiftKey && ['i', 'I', 'j', 'J', 'c', 'C'].includes(e.key)) ||
      (e.ctrlKey && ['u', 'U'].includes(e.key))
    ) {
      e.preventDefault()
      onViolationCallback('devtools', `Blocked keyboard shortcut: Ctrl+${e.shiftKey ? 'Shift+' : ''}${e.key}`, 'high')
    }
  }

  function start(onViolation: (type: string, desc: string, severity: string) => void) {
    onViolationCallback = onViolation
    isActive.value = true
    tabSwitchesCount.value = 0

    // Fullscreen
    document.addEventListener('fullscreenchange', handleFullscreenChange)
    
    // Visibility/Blur
    document.addEventListener('visibilitychange', handleVisibilityChange)
    window.addEventListener('blur', handleWindowBlur)

    // Copy Paste context menu
    document.addEventListener('copy', preventCopyPaste)
    document.addEventListener('cut', preventCopyPaste)
    document.addEventListener('paste', preventCopyPaste)
    document.addEventListener('contextmenu', preventContextMenu)

    // Keyboard shortcuts
    window.addEventListener('keydown', handleKeyDown)

    // Trigger initial fullscreen request
    enforceFullscreen()
  }

  function stop() {
    isActive.value = false

    document.removeEventListener('fullscreenchange', handleFullscreenChange)
    document.removeEventListener('visibilitychange', handleVisibilityChange)
    window.removeEventListener('blur', handleWindowBlur)
    
    document.removeEventListener('copy', preventCopyPaste)
    document.removeEventListener('cut', preventCopyPaste)
    document.removeEventListener('paste', preventCopyPaste)
    document.removeEventListener('contextmenu', preventContextMenu)

    window.removeEventListener('keydown', handleKeyDown)

    // Exit fullscreen if still active
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => {})
    }
  }

  onUnmounted(stop)

  return {
    isFullscreen,
    tabSwitchesCount,
    isActive,
    start,
    stop,
    enforceFullscreen
  }
}
