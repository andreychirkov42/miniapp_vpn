import { getInitData } from './telegram'
import type {
  ConfigResponse,
  DeviceListResponse,
  MeResponse,
  Subscription,
  SupportResponse,
  TicketDetail,
  TicketListResponse,
} from './types'

// Пусто → относительный путь (тот же origin, что и фронт — режим одного туннеля).
// В dev переопределяется через .env (VITE_API_BASE=http://localhost:8000).
const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  // FormData сам выставляет multipart-заголовок с boundary — Content-Type не трогаем.
  const isForm = init?.body instanceof FormData
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      ...(isForm ? {} : { 'Content-Type': 'application/json' }),
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

// Картинку-вложение нельзя отдать через <img src> (тег не шлёт Authorization),
// поэтому грузим её fetch'ем с initData и отдаём object URL для отрисовки.
async function fetchAttachment(path: string): Promise<string> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { Authorization: `tma ${getInitData()}` },
  })
  if (!res.ok) throw new Error('attachment load failed')
  return URL.createObjectURL(await res.blob())
}

function supportForm(message: string, file?: File | null, ticketId?: number): FormData {
  const form = new FormData()
  form.append('message', message)
  if (ticketId) form.append('ticket_id', String(ticketId))
  if (file) form.append('file', file)
  return form
}

export const api = {
  me: () => request<MeResponse>('/api/me'),
  activateTrial: () => request<Subscription>('/api/trial', { method: 'POST' }),
  renew: (uuid: string) =>
    request<Subscription>(`/api/subscriptions/${uuid}/renew`, { method: 'POST' }),
  config: (uuid: string) => request<ConfigResponse>(`/api/subscriptions/${uuid}/config`),
  devices: (uuid: string) => request<DeviceListResponse>(`/api/subscriptions/${uuid}/devices`),
  deleteDevice: (uuid: string, hwid: string) =>
    request<DeviceListResponse>(`/api/subscriptions/${uuid}/devices/delete`, {
      method: 'POST',
      body: JSON.stringify({ hwid }),
    }),
  // ticketId не задан → создаётся новое обращение; иначе — дописываем в тред.
  // Можно отправить текст и/или картинку-вложение.
  support: (message: string, ticketId?: number, file?: File | null) =>
    request<SupportResponse>('/api/support', {
      method: 'POST',
      body: supportForm(message, file, ticketId),
    }),
  myTickets: () => request<TicketListResponse>('/api/support/tickets'),
  myTicket: (id: number) => request<TicketDetail>(`/api/support/tickets/${id}`),
  attachment: fetchAttachment,

  admin: {
    tickets: (onlyActive = true) =>
      request<TicketListResponse>(`/api/admin/support/tickets?only_active=${onlyActive}`),
    ticket: (id: number) => request<TicketDetail>(`/api/admin/support/tickets/${id}`),
    reply: (id: number, message: string, file?: File | null) => {
      const form = new FormData()
      form.append('message', message)
      if (file) form.append('file', file)
      return request<TicketDetail>(`/api/admin/support/tickets/${id}/reply`, {
        method: 'POST',
        body: form,
      })
    },
    close: (id: number) =>
      request<TicketDetail>(`/api/admin/support/tickets/${id}/close`, { method: 'POST' }),
  },
}
