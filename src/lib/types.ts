// Зеркало pydantic-схем бэкенда (snake_case как в JSON-ответе FastAPI).

export type Subscription = {
  id: string
  uuid: string
  label: string
  name: string
  status: string
  pro: boolean
  used_traffic_bytes: number
  traffic_limit_bytes: number
  traffic_text: string | null
  expire_at: string
  expire_text: string
  expired: boolean
  devices_used: number
  device_limit: number
  devices_text: string
  subscription_url: string
}

export type MeResponse = {
  telegram_id: number
  subscriptions: Subscription[]
  is_admin: boolean
  trial_days: number
}

export type ConfigResponse = {
  subscription_url: string
}

export type Device = {
  hwid: string
  platform: string
  device_model: string
  created_at: string | null
}

export type DeviceListResponse = {
  devices: Device[]
}

export type SupportResponse = {
  ok: boolean
  ticket_id: number
}

export type TicketStatus = 'open' | 'answered' | 'closed'

export type Ticket = {
  id: number
  status: TicketStatus
  created_at: string
  updated_at: string
  last_message: string | null
  last_author: 'user' | 'admin' | null
  // присутствует в админских ответах
  user_telegram_id?: number | null
  username?: string | null
  first_name?: string | null
}

export type TicketMessage = {
  id: number
  author: 'user' | 'admin'
  text: string
  created_at: string
  // путь защищённого эндпоинта с картинкой-вложением (фронт догружает с initData)
  attachment_url?: string | null
}

export type TicketDetail = Ticket & {
  messages: TicketMessage[]
}

export type TicketListResponse = {
  tickets: Ticket[]
}
