import { getInitData } from './telegram'
import type { ConfigResponse, MeResponse, Subscription } from './types'

// Пусто → относительный путь (тот же origin, что и фронт — режим одного туннеля).
// В dev переопределяется через .env (VITE_API_BASE=http://localhost:8000).
const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      // initData аутентифицирует пользователя на бэкенде; в браузере пусто → dev-fallback
      Authorization: `tma ${getInitData()}`,
      ...(init?.headers ?? {}),
    },
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      detail = (await res.json()).detail ?? detail
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

export const api = {
  me: () => request<MeResponse>('/api/me'),
  activateTrial: () => request<Subscription>('/api/trial', { method: 'POST' }),
  renew: (uuid: string) =>
    request<Subscription>(`/api/subscriptions/${uuid}/renew`, { method: 'POST' }),
  config: (uuid: string) => request<ConfigResponse>(`/api/subscriptions/${uuid}/config`),
}
