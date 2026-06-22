import { useCallback, useEffect, useState } from 'react'
import { api } from '../lib/api'
import type { Subscription } from '../lib/types'

// Дефолт срока триала на случай ошибки загрузки — переопределяется значением с бэка.
const DEFAULT_TRIAL_DAYS = 7

type State = {
  subs: Subscription[]
  isAdmin: boolean
  trialDays: number
  loading: boolean
  error: string | null
}

export function useSubscriptions() {
  const [state, setState] = useState<State>({
    subs: [],
    isAdmin: false,
    trialDays: DEFAULT_TRIAL_DAYS,
    loading: true,
    error: null,
  })

  const load = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const me = await api.me()
      setState({
        subs: me.subscriptions,
        isAdmin: me.is_admin,
        trialDays: me.trial_days,
        loading: false,
        error: null,
      })
    } catch (e) {
      setState((s) => ({ ...s, subs: [], isAdmin: false, loading: false, error: (e as Error).message }))
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const activateTrial = useCallback(async () => {
    const created = await api.activateTrial()
    await load()
    return created
  }, [load])

  const renew = useCallback(
    async (uuid: string) => {
      const updated = await api.renew(uuid)
      await load()
      return updated
    },
    [load],
  )

  return { ...state, reload: load, activateTrial, renew }
}
