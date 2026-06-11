import { useCallback, useEffect, useState } from 'react'
import { api } from '../lib/api'
import type { Subscription } from '../lib/types'

type State = {
  subs: Subscription[]
  loading: boolean
  error: string | null
}

export function useSubscriptions() {
  const [state, setState] = useState<State>({ subs: [], loading: true, error: null })

  const load = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const me = await api.me()
      setState({ subs: me.subscriptions, loading: false, error: null })
    } catch (e) {
      setState({ subs: [], loading: false, error: (e as Error).message })
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
