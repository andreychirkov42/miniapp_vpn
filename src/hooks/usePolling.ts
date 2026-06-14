import { useCallback, useEffect, useRef, useState } from 'react'

type State<T> = {
  data: T | null
  loading: boolean
  error: string | null
}

// Периодически дёргает fetcher (для лент обращений/треда). Очищает таймер при
// размонтировании и пропускает setState после unmount. Управляется флагом enabled.
// deps — значения, при смене которых нужен немедленный перезапрос (напр. фильтр
// ленты): без них смена параметра fetcher подхватилась бы лишь на следующем тике.
export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs: number,
  enabled = true,
  deps: readonly unknown[] = [],
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
    // deps добавлены намеренно (динамический список) — exhaustive-deps их не видит.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, intervalMs, refresh, ...deps])

  return { ...state, refresh }
}
