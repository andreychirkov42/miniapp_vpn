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
}

export type ConfigResponse = {
  subscription_url: string
  deeplinks: Record<string, string>
}
