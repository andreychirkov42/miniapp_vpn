import { useCallback, useEffect, useRef, useState } from 'react'

type State<T> = {
  data: T | null
  loading: boolean
  error: string | null
}

// Периодически дёргает fetcher (для лент обращений/треда). Очищает таймер при
// размонтировании и пропускает setState после unmount. Управляется флагом enabled.
export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs: number,
  enabled = true,
): State<T> & { refresh: () => Promise<void> } {
  const [state, setState] = useState<State<T>>({ data: null, loading: true, error: null })
  const fetcherRef = useRef(fetcher)
  fetcherRef.current = fetcher
  const aliveRef = useRef(true)

  const refresh = useCallback(async () => {
    try {
      const data = await fetcherRef.current()
      if (aliveRef.current) setState({ data, loading: false, error: null })
    } catch (e) {
      if (aliveRef.current)
        setState((s) => ({ ...s, loading: false, error: (e as Error).message }))
    }
  }, [])

  useEffect(() => {
    aliveRef.current = true
    if (!enabled) return
    void refresh()
    const id = setInterval(() => void refresh(), intervalMs)
    return () => {
      aliveRef.current = false
      clearInterval(id)
    }
  }, [enabled, intervalMs, refresh])

  return { ...state, refresh }
}
