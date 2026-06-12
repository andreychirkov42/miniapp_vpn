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

export function getInitData(): string {
  return tg()?.initData ?? ''
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

export function getUserId(): number | null {
  return tg()?.initDataUnsafe?.user?.id ?? null
}

export function shareToTelegram(url: string, text: string): void {
  const share = `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`
  const w = tg()
  if (w?.openTelegramLink) w.openTelegramLink(share)
  else window.open(share, '_blank')
}
