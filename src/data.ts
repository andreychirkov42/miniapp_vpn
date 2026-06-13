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

export type PlatformId = 'ios' | 'android' | 'windows' | 'macos'

export type PlatformApp = {
  id: PlatformId
  label: string // показывается пользователю: "iPhone / iPad"
  short: string // краткое: "iOS"
  app: string // название клиента (1 на платформу) — заменишь на финальный
  downloadUrl: string // ссылка на скачивание приложения — заполнишь
  // шаблон диплинка импорта подписки; {url} → subscription_url
  deeplink: string
}

// Схемы импорта подписки:
//  - FlClashX (Android/Win/macOS): flclashx://install-config?url=<encoded> (сверено с конфигом Remnawave)
//  - RabbitHole (iOS): rabbithole://add/<subscription_url> — подтверждено тестом (вар.6)
// Открываются не напрямую (Telegram WebView гасит кастомные схемы), а через
// https-мост /open — см. PlatformInstall.connect().
const FLCLASH_DEEPLINK = 'flclashx://install-config?url={url}' // url кодируется (стоит после "=")
const RABBITHOLE_DEEPLINK = 'rabbithole://add/{url}' // url как путь, без кодирования

export const platformApps: PlatformApp[] = [
  { id: 'ios', label: 'iPhone / iPad', short: 'iOS', app: 'RabbitHole', downloadUrl: 'https://apps.apple.com/us/app/rabbithole-vpn-client/id6683309629', deeplink: RABBITHOLE_DEEPLINK },
  { id: 'android', label: 'Android', short: 'Android', app: 'FlClashX', downloadUrl: 'https://github.com/pluralplay/FlClashX/releases/download/v0.3.2/FlClashX-android-universal.apk', deeplink: FLCLASH_DEEPLINK },
  { id: 'windows', label: 'Windows', short: 'Windows', app: 'FlClashX', downloadUrl: 'https://github.com/pluralplay/FlClashX/releases/download/v0.3.2/FlClashX-windows-amd64-setup.exe', deeplink: FLCLASH_DEEPLINK },
  { id: 'macos', label: 'macOS', short: 'macOS', app: 'FlClashX', downloadUrl: 'https://github.com/pluralplay/FlClashX/releases/download/v0.3.2/FlClashX-macos-arm64.dmg', deeplink: FLCLASH_DEEPLINK },
]

export const BOT_USERNAME = 'bezgraniz_cabinet_bot'
export const REFERRAL_BONUS_DAYS = 10

export type Payment = {
  id: string
  date: string
  amount: string
  title: string
  status: 'ok' | 'pending' | 'failed'
}

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

// Единый список профиля (без секций). Без «Вход в систему» и «Добавить на рабочий стол».
export const profileList: ProfileItem[] = [
  { id: 'promo', title: 'Применить промокод', icon: 'gift' },
  { id: 'referral', title: 'Реферальная система', icon: 'heart' },
  { id: 'partner', title: 'Партнёрская программа', icon: 'wallet' },
  { id: 'payments', title: 'Платежи', icon: 'card' },
  { id: 'news', title: 'Новости', icon: 'rss' },
  { id: 'channel', title: 'Канал', icon: 'send' },
  { id: 'faq', title: 'Часто задаваемые вопросы', icon: 'question' },
  { id: 'privacy', title: 'Политика конфиденциальности', icon: 'shield' },
  { id: 'terms', title: 'Пользовательское соглашение', icon: 'doc' },
]
