import { useCallback, useRef, useState } from 'react'

export type ToastKind = 'error' | 'success' | 'info'

export interface Toast {
  id: number
  kind: ToastKind
  message: string
}

const DEFAULT_DURATION = 6000

export function useToasts() {
  const [toasts, setToasts] = useState<Toast[]>([])
  const nextId = useRef(1)

  const dismiss = useCallback((id: number) => {
    setToasts((list) => list.filter((t) => t.id !== id))
  }, [])

  const push = useCallback(
    (
      message: string,
      kind: ToastKind = 'error',
      duration = DEFAULT_DURATION,
    ) => {
      const id = nextId.current++
      setToasts((list) => [...list, { id, kind, message }])
      if (duration > 0) {
        setTimeout(() => dismiss(id), duration)
      }
      return id
    },
    [dismiss],
  )

  return { toasts, push, dismiss }
}
