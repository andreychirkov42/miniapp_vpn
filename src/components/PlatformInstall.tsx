import { useMemo, useState } from 'react'
import { platformApps } from '../data'
import { detectPlatform } from '../lib/platform'
import { openExternal } from '../lib/telegram'
import { IconCheck, IconDownload, IconPlug } from '../icons'

// Двухшаговый мастер подключения:
//  1) «Установить» — скачать приложение под платформу → «Уже установил».
//  2) «Добавить подписку» — импорт конфига в клиент по deeplink (ссылка не показывается).
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
    if (!subscriptionUrl) return
    // если {url} стоит после "=" (query-параметр) — кодируем; иначе вставляем как есть
    const i = app.deeplink.indexOf('{url}')
    const value = i > 0 && app.deeplink[i - 1] === '=' ? encodeURIComponent(subscriptionUrl) : subscriptionUrl
    openExternal(app.deeplink.replace('{url}', value))
  }

  return (
    <div className="pinstall">
      <div className="stepper">
        <div className={`stepper__item ${step === 'add' ? 'is-done' : 'is-on'}`}>
          <span className="stepper__num">{step === 'add' ? <IconCheck size={14} /> : '1'}</span>
          <span className="stepper__label">Установить</span>
        </div>
        <span className={`stepper__line ${step === 'add' ? 'is-filled' : ''}`} />
        <div className={`stepper__item ${step === 'add' ? 'is-on' : ''}`}>
          <span className="stepper__num">2</span>
          <span className="stepper__label">Подписка</span>
        </div>
      </div>

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
          <div className="pinstall__ready">
            <span className="pinstall__ready-ic">
              <IconCheck size={20} />
            </span>
            <div className="pinstall__ready-text">
              <span className="pinstall__ready-title">{app.app} установлен</span>
              <span className="pinstall__ready-note">Подключим подписку в один тап</span>
            </div>
          </div>

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
