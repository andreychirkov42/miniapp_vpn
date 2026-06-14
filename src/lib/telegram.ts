// Тонкая обёртка над Telegram WebApp SDK (telegram-web-app.js).

type TgWebApp = {
  initData: string
  initDataUnsafe?: { user?: { id: number; first_name?: string; username?: string } }
  ready: () => void
  expand: () => void
  openLink: (url: string) => void
  openTelegramLink: (url: string) => void
  HapticFeedback?: { impactOccurred: (s: string) => void; notificationOccurred: (s: string) => void }
  colorScheme?: string
  platform?: string
  onEvent?: (event: string, handler: () => void) => void
  offEvent?: (event: string, handler: () => void) => void
}

export function tg(): TgWebApp | null {
  return (window as unknown as { Telegram?: { WebApp?: TgWebApp } }).Telegram?.WebApp ?? null
}

export function initTelegram(): void {
  const w = tg()
  if (!w) return
  try {
    w.ready()
    w.expand()
  } catch {
    /* not in Telegram — ignore */
  }
}

const INIT_DATA_KEY = 'tg_init_data'

// initData нужен бэкенду для проверки подписи и идентификации пользователя.
// Проблема: при запуске мини-аппа через меню-кнопку (и в Telegram Desktop)
// Telegram.WebApp.initData нередко приходит пустым, хотя через inline-кнопку он есть.
// Поэтому берём данные из нескольких источников по убыванию надёжности:
//  1) живой WebApp.initData;
//  2) launch-параметр tgWebAppData из URL-фрагмента (его парсит сам SDK);
//  3) последний валидный initData этого устройства (бэкенд не проверяет срок —
//     своя же подписанная строка остаётся валидной, юзер тот же).
export function getInitData(): string {
  const live = tg()?.initData ?? ''
  if (live) {
    cacheInitData(live)
    return live
  }
  const fromHash = initDataFromHash()
  if (fromHash) {
    cacheInitData(fromHash)
    return fromHash
  }
  try {
    return localStorage.getItem(INIT_DATA_KEY) ?? ''
  } catch {
    return ''
  }
}

function cacheInitData(value: string): void {
  try {
    localStorage.setItem(INIT_DATA_KEY, value)
  } catch {
    /* localStorage недоступен — не критично */
  }
}

function initDataFromHash(): string {
  try {
    const hash = window.location.hash.replace(/^#/, '')
    return new URLSearchParams(hash).get('tgWebAppData') ?? ''
  } catch {
    return ''
  }
}

export function haptic(kind: 'light' | 'success' | 'error' = 'light'): void {
  const h = tg()?.HapticFeedback
  if (!h) return
  if (kind === 'light') h.impactOccurred('light')
  else h.notificationOccurred(kind)
}

export function openExternal(url: string): void {
  const w = tg()
  if (w?.openLink) w.openLink(url)
  else window.open(url, '_blank')
}

// Открыть Telegram-бота кабинета (когда мини-апп запущен вне Telegram).
export function openBot(username: string): void {
  const url = `https://t.me/${username}`
  const w = tg()
  if (w?.openTelegramLink) w.openTelegramLink(url)
  else window.open(url, '_blank')
}

export function getUserId(): number | null {
  return tg()?.initDataUnsafe?.user?.id ?? null
}

// Скопировать текст в буфер обмена. СИНХРОННО — чтобы не потерять «жест
// пользователя»: в WebView Telegram Desktop `await navigator.clipboard` рвёт
// активацию и фолбэк execCommand уже не срабатывает. Поэтому сначала
// execCommand в рамках клика, а navigator.clipboard — как доп. попытка.
export function copyToClipboard(text: string): boolean {
  let ok = false
  try {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.setAttribute('readonly', '')
    ta.style.position = 'fixed'
    ta.style.left = '-9999px'
    document.body.appendChild(ta)
    ta.select()
    ta.setSelectionRange(0, text.length)
    try {
      ok = document.execCommand('copy')
    } catch {
      ok = false
    }
    document.body.removeChild(ta)
  } catch {
    ok = false
  }
  if (!ok && navigator.clipboard?.writeText) {
    navigator.clipboard.writeText(text).catch(() => {})
  }
  return ok
}

export function shareToTelegram(url: string, text: string): void {
  const share = `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`
  const w = tg()
  if (w?.openTelegramLink) w.openTelegramLink(share)
  else window.open(share, '_blank')
}
