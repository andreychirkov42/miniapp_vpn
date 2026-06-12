import { useMemo, useState } from 'react'
import { platformApps, type PlatformId } from '../data'
import { detectPlatform } from '../lib/platform'
import { openExternal } from '../lib/telegram'
import { IconChevronDown, IconDownload, IconPlug } from '../icons'

// Установка приложения под платформу пользователя.
// Основная кнопка — скачать приложение; вторая (если есть ссылка подписки) — импорт конфига.
export default function PlatformInstall({ subscriptionUrl }: { subscriptionUrl?: string }) {
  const detected = useMemo(detectPlatform, [])
  const [pid, setPid] = useState<PlatformId>(detected)
  const [open, setOpen] = useState(false)
  const [hint, setHint] = useState<string | null>(null)

  const app = platformApps.find((p) => p.id === pid) ?? platformApps[0]

  const download = () => {
    if (app.downloadUrl) openExternal(app.downloadUrl)
    else setHint(`Ссылка для «${app.label}» скоро будет добавлена`)
  }

  const connect = () => {
    if (!subscriptionUrl) return
    // если {url} стоит после "=" (query-параметр, как у clash) — кодируем; иначе вставляем как есть
    const i = app.deeplink.indexOf('{url}')
    const value = i > 0 && app.deeplink[i - 1] === '=' ? encodeURIComponent(subscriptionUrl) : subscriptionUrl
    openExternal(app.deeplink.replace('{url}', value))
  }

  return (
    <div className="pinstall">
      <button className="pinstall__pick" onClick={() => setOpen((v) => !v)}>
        <span>
          Платформа: <b>{app.label}</b>
        </span>
        <IconChevronDown size={18} />
      </button>

      {open && (
        <div className="pinstall__menu">
          {platformApps.map((p) => (
            <button
              key={p.id}
              className={`pinstall__opt ${p.id === pid ? 'pinstall__opt--active' : ''}`}
              onClick={() => {
                setPid(p.id)
                setOpen(false)
                setHint(null)
              }}
            >
              {p.label}
            </button>
          ))}
        </div>
      )}

      <button className="btn btn-primary btn-lg" onClick={download}>
        <IconDownload size={22} />
        Установить
      </button>

      {subscriptionUrl && (
        <button className="btn btn-secondary btn-lg" onClick={connect}>
          <IconPlug size={20} />
          Подключить подписку
        </button>
      )}

      {hint && <div className="cfg-hint">{hint}</div>}
    </div>
  )
}
