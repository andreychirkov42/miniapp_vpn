// Тема приложения следует за темой устройства: внутри Telegram — за colorScheme
// мини-аппа (он повторяет системную), вне Telegram — за prefers-color-scheme браузера.
// Активная тема выставляется атрибутом data-theme на <html>, дальше всё решает CSS.

import { tg } from './telegram'

type Scheme = 'light' | 'dark'

function currentScheme(): Scheme {
  const tgScheme = tg()?.colorScheme
  if (tgScheme === 'dark' || tgScheme === 'light') return tgScheme
  if (window.matchMedia?.('(prefers-color-scheme: dark)').matches) return 'dark'
  return 'light'
}

function apply(scheme: Scheme): void {
  document.documentElement.dataset.theme = scheme
}

// Ставит тему сразу и подписывается на её смену (Telegram themeChanged + системная).
// Вызывается один раз на старте приложения; живёт всё время сессии.
export function initTheme(): void {
  apply(currentScheme())
  const sync = () => apply(currentScheme())

  tg()?.onEvent?.('themeChanged', sync)
  window.matchMedia?.('(prefers-color-scheme: dark)').addEventListener?.('change', sync)
}
