import { useMemo, useState } from 'react'
import { platformApps, type PlatformId } from '../data'
import { detectPlatform } from '../lib/platform'
import { openExternal } from '../lib/telegram'
import { IconChevronDown, IconDownload, IconPlug } from '../icons'

// Двухшаговый мастер подключения:
//  1) «Установить» — скачать приложение под платформу → «Уже установил».
//  2) «Добавить подписку» — импорт конфига в клиент по deeplink (ссылка не показывается).
export default function PlatformInstall({ subscriptionUrl }: { subscriptionUrl?: string }) {
  const detected = useMemo(detectPlatform, [])
  const [pid, setPid] = useState<PlatformId>(detected)
  const [open, setOpen] = useState(false)
  const [step, setStep] = useState<'install' | 'add'>('install')
  const [hint, setHint] = useState<string | null>(null)

  const app = platformApps.find((p) => p.id === pid) ?? platformApps[0]

  const download = () => {
    if (app.downloadUrl) openExternal(app.downloadUrl)
    else setHint(`Ссылка для «${app.label}» скоро будет добавлена`)
  }

  const connect = () => {
    if (!subscriptionUrl) return
    // если {url} стоит после "=" (query-параметр) — кодируем; иначе вставляем как есть
    const i = app.deeplink.indexOf('{url}')
    const value = i > 0 && app.deeplink[i - 1] === '=' ? encodeURIComponent(subscriptionUrl) : subscriptionUrl
    openExternal(app.deeplink.replace('{url}', value))
  }

  return (
    <div className="pinstall">
      <div className="pinstall__steps">
        <span className={`pinstall__step ${step === 'install' ? 'pinstall__step--on' : ''}`}>1. Установить</span>
        <span className="pinstall__dash" />
        <span className={`pinstall__step ${step === 'add' ? 'pinstall__step--on' : ''}`}>2. Подписка</span>
      </div>

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

      {step === 'install' ? (
        <>
          <button className="btn btn-primary btn-lg" onClick={download}>
            <IconDownload size={22} />
            Установить {app.app}
          </button>
          <button
            className="btn btn-secondary btn-lg"
            onClick={() => {
              setStep('add')
              setHint(null)
            }}
          >
            Уже установил
          </button>
        </>
      ) : (
        <>
          <button className="btn btn-primary btn-lg" onClick={connect} disabled={!subscriptionUrl}>
            <IconPlug size={20} />
            Добавить подписку
          </button>
          <button className="btn-text" onClick={() => setStep('install')}>
            Назад к установке
          </button>
        </>
      )}

      {hint && <div className="cfg-hint">{hint}</div>}
    </div>
  )
}
