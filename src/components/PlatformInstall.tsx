import { useMemo, useState } from 'react'
import { platformApps } from '../data'
import { detectPlatform } from '../lib/platform'
import { openExternal, copyToClipboard } from '../lib/telegram'
import { IconDownload, IconPlug } from '../icons'

// Двухшаговый мастер подключения:
//  1) «Установить {app}» — скачать клиент под платформу → «Клиент установлен».
//  2) «Добавить подписку» — импорт конфига в клиент через https-мост /open.
export default function PlatformInstall({ subscriptionUrl }: { subscriptionUrl?: string }) {
  const pid = useMemo(detectPlatform, [])
  const [step, setStep] = useState<'install' | 'add'>('install')
  const [hint, setHint] = useState<string | null>(null)

  const app = platformApps.find((p) => p.id === pid) ?? platformApps[0]

  const download = () => {
    if (app.downloadUrl) openExternal(app.downloadUrl)
    else setHint(`Ссылка для «${app.label}» скоро будет добавлена`)
  }

  const connect = () => {
    if (!subscriptionUrl) {
      setHint('Подписка ещё не готова — обновите экран чуть позже')
      return
    }
    // Подставляем ссылку подписки СЫРОЙ — байт-в-байт как Remnawave подставляет
    // {{SUBSCRIPTION_LINK}} в app-config панели (это проверенная рабочая форма;
    // ссылки подписки чистые, без query-параметров, кодировать нечего).
    const deeplink = app.deeplink.replace('{url}', subscriptionUrl)
    // Telegram WebView не пускает кастомные схемы напрямую, поэтому открываем
    // https-мост /open: он редиректит в схему уже из браузера → ОС запускает клиент.
    const bridge = `${window.location.origin}/open?to=${encodeURIComponent(deeplink)}`
    openExternal(bridge)
    setHint(`Открываем ${app.app}… не открылось — установите клиент и повторите или скопируйте ссылку`)
  }

  const copyLink = () => {
    if (!subscriptionUrl) {
      setHint('Подписка ещё не готова — обновите экран чуть позже')
      return
    }
    const ok = copyToClipboard(subscriptionUrl)
    setHint(ok ? 'Ссылка скопирована — вставьте её в клиент' : 'Выделите ссылку выше и скопируйте вручную')
  }

  // ---- Шаг 1: установка клиента ----
  if (step === 'install') {
    return (
      <div className="pinstall">
        <div className="pinstall__lead">
          Установите клиент <b>{app.app}</b> для {app.label}, затем добавьте подписку.
        </div>
        <button className="btn btn-primary btn-lg" onClick={download}>
          <IconDownload size={22} />
          Установить
        </button>
        <button
          className="btn btn-secondary btn-lg"
          onClick={() => {
            setStep('add')
            setHint(null)
          }}
        >
          <IconPlug size={20} />
          Клиент установлен — добавить подписку
        </button>
        {hint && <div className="cfg-hint">{hint}</div>}
      </div>
    )
  }

  // ---- Шаг 2: добавление подписки ----
  return (
    <div className="pinstall">
      <div className="pinstall__lead">
        Подписка для <b>{app.app}</b> готова — добавьте её в клиент.
      </div>
      <button className="btn btn-primary btn-lg" onClick={connect} disabled={!subscriptionUrl}>
        <IconPlug size={20} />
        Добавить подписку
      </button>

      {subscriptionUrl && (
        <div className="sub-link">
          <button className="btn btn-secondary btn-lg" onClick={copyLink}>
            Скопировать ссылку
          </button>
          <div className="sub-link__note">
            Не открылось автоматически? Скопируйте ссылку и вставьте её в {app.app}: «Добавить из буфера обмена».
          </div>
        </div>
      )}

      <button
        className="btn-text"
        onClick={() => {
          setStep('install')
          setHint(null)
        }}
      >
        Назад к установке
      </button>
      {hint && <div className="cfg-hint">{hint}</div>}
    </div>
  )
}
