import { useMemo, useState } from 'react'
import { platformApps } from '../data'
import { detectPlatform } from '../lib/platform'
import { openDeeplink, openExternal } from '../lib/telegram'
import { IconCheck, IconDownload, IconPlug } from '../icons'

// Подключение в один тап: основное действие — «Добавить подписку» (импорт конфига
// в клиент по deeplink). Если клиент ещё не установлен — вторичный шаг установки.
export default function PlatformInstall({ subscriptionUrl }: { subscriptionUrl?: string }) {
  const pid = useMemo(detectPlatform, [])
  const [step, setStep] = useState<'add' | 'install'>('add')
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
    // если {url} стоит после "=" (query-параметр) — кодируем; иначе вставляем как есть
    const i = app.deeplink.indexOf('{url}')
    const value =
      i > 0 && app.deeplink[i - 1] === '=' ? encodeURIComponent(subscriptionUrl) : subscriptionUrl
    openDeeplink(app.deeplink.replace('{url}', value))
  }

  if (step === 'install') {
    return (
      <div className="pinstall">
        <div className="pinstall__lead">
          Установите клиент <b>{app.app}</b> для {app.label}, затем вернитесь и добавьте подписку.
        </div>
        <button className="btn btn-primary btn-lg" onClick={download}>
          <IconDownload size={22} />
          Установить {app.app}
        </button>
        <button className="btn btn-secondary btn-lg" onClick={() => { setStep('add'); setHint(null) }}>
          <IconPlug size={20} />
          Клиент установлен — добавить подписку
        </button>
        {hint && <div className="cfg-hint">{hint}</div>}
      </div>
    )
  }

  return (
    <div className="pinstall">
      <div className="pinstall__ready">
        <span className="pinstall__ready-ic">
          <IconCheck size={20} />
        </span>
        <div className="pinstall__ready-text">
          <span className="pinstall__ready-title">Подписка готова</span>
          <span className="pinstall__ready-note">Откроется в {app.app} в один тап</span>
        </div>
      </div>

      <button className="btn btn-primary btn-lg" onClick={connect} disabled={!subscriptionUrl}>
        <IconPlug size={20} />
        Добавить подписку
      </button>
      <button className="btn-text" onClick={() => { setStep('install'); setHint(null) }}>
        Клиент ещё не установлен?
      </button>

      {hint && <div className="cfg-hint">{hint}</div>}
    </div>
  )
}
