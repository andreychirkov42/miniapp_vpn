export type Subscription = {
  id: string
  label: string
  name: string
  expires: string
  devices: string
  traffic?: string
  pro: boolean
}

export const subscriptions: Subscription[] = [
  {
    id: 'main',
    label: 'Основная',
    name: 'Pro',
    expires: '14.06.2026',
    devices: '0/∞ устройств',
    pro: true,
  },
  {
    id: '100564',
    label: 'Подписка #100564',
    name: 'Whitelist',
    expires: '14.06.2026',
    devices: '0/∞ устройств',
    traffic: '0/5 GB',
    pro: false,
  },
]

export type SupportAction = {
  id: string
  title: string
  sub: string
  icon: 'plus' | 'question' | 'devices'
}

export const supportActions: SupportAction[] = [
  { id: 'new', title: 'Новое обращение', sub: 'Связаться с поддержкой', icon: 'plus' },
  { id: 'faq', title: 'Часто задаваемые вопросы', sub: 'Ответы на часто задаваемые вопросы', icon: 'question' },
  {
    id: 'install',
    title: 'Установка на другом устройстве',
    sub: 'Подробная инструкция для установки',
    icon: 'devices',
  },
]

export type Platform = {
  id: string
  label: string
  url: string // store/download link — заполняется позже
}

export const installPlatforms: Platform[] = [
  { id: 'ios', label: 'iPhone / iPad', url: '' },
  { id: 'android', label: 'Android', url: '' },
  { id: 'windows', label: 'Windows', url: '' },
  { id: 'macos', label: 'macOS', url: '' },
  { id: 'androidtv', label: 'Android TV', url: '' },
  { id: 'linux', label: 'Linux', url: '' },
]

export type ProfileItem = {
  id: string
  title: string
  icon:
    | 'gift'
    | 'rss'
    | 'send'
    | 'shield'
    | 'doc'
    | 'heart'
    | 'wallet'
    | 'export'
    | 'question'
    | 'login'
    | 'card'
}

export const profileItems: ProfileItem[] = [
  { id: 'promo', title: 'Применить промокод', icon: 'gift' },
  { id: 'news', title: 'Новости', icon: 'rss' },
  { id: 'channel', title: 'Канал', icon: 'send' },
  { id: 'privacy', title: 'Политика конфиденциальности', icon: 'shield' },
  { id: 'terms', title: 'Пользовательское соглашение', icon: 'doc' },
  { id: 'referral', title: 'Реферальная система', icon: 'heart' },
  { id: 'partner', title: 'Партнёрская программа', icon: 'wallet' },
  { id: 'desktop', title: 'Добавить на рабочий стол', icon: 'export' },
  { id: 'faq', title: 'Часто задаваемые вопросы', icon: 'question' },
  { id: 'login', title: 'Вход в систему', icon: 'login' },
  { id: 'payments', title: 'Платежи', icon: 'card' },
]
