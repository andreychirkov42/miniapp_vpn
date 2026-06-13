import { tg } from './telegram'
import type { PlatformId } from '../data'

// Определяем платформу пользователя: сначала по Telegram WebApp.platform,
// затем по userAgent. Возвращаем id из data.platformApps.
export function detectPlatform(): PlatformId {
  const p = (tg()?.platform || '').toLowerCase()
  if (p === 'ios') return 'ios'
  if (p === 'android') return 'android'
  if (p === 'macos') return 'macos'
  if (p === 'windows' || p === 'win') return 'windows'
  // 'tdesktop' (десктопный Telegram) — это Windows/macOS/Linux, различаем по userAgent ниже.

  const ua = (navigator.userAgent || '').toLowerCase()
  if (/iphone|ipad|ipod/.test(ua)) return 'ios'
  if (/android/.test(ua)) return 'android' // android UA тоже содержит "linux" — проверяем раньше
  if (/macintosh|mac os x/.test(ua)) return 'macos'
  if (/windows|win64|win32/.test(ua)) return 'windows'
  if (/linux|x11/.test(ua)) return 'linux'
  return 'android'
}
