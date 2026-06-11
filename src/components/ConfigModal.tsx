import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import type { ConfigResponse, Subscription } from '../lib/types'
import { openExternal } from '../lib/telegram'
import { IconClose, IconGear } from '../icons'

const CLIENT_LABELS: Record<string, string> = {
  v2raytun: 'v2RayTun',
  happ: 'Happ',
  streisand: 'Streisand',
  hiddify: 'Hiddify',
  clash: 'Clash',
}

export default function ConfigModal({
  sub,
  onClose,
  title = 'Установить и настроить',
}: {
  sub: Subscription
  onClose: () => void
  title?: string
}) {
  const [cfg, setCfg] = useState<ConfigResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    api
      .config(sub.uuid)
      .then(setCfg)
      .catch((e) => setError((e as Error).message))
  }, [sub.uuid])

  const copy = async () => {
    if (!cfg) return
    try {
      await navigator.clipboard.writeText(cfg.subscription_url)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal modal--config" onClick={(e) => e.stopPropagation()}>
        <button className="modal__close" onClick={onClose} aria-label="close">
          <IconClose size={22} />
        </button>
        <span className="modal__icon">
          <IconGear size={36} />
        </span>
        <div className="modal__title" style={{ fontSize: 22 }}>
          {title}
        </div>
        <div className="modal__sub">Подписка «{sub.name}». Скопируйте ссылку или откройте в приложении.</div>

        {error && <div className="cfg-error">{error}</div>}

        {cfg && (
          <>
            <button className="cfg-url" onClick={copy}>
              <span>{cfg.subscription_url}</span>
              <b>{copied ? 'Скопировано' : 'Копировать'}</b>
            </button>

            <div className="cfg-clients">
              {Object.entries(cfg.deeplinks).map(([key, url]) => (
                <button key={key} className="cfg-client" onClick={() => openExternal(url)}>
                  {CLIENT_LABELS[key] ?? key}
                </button>
              ))}
            </div>
          </>
        )}

        <button className="btn-text" onClick={onClose}>
          Закрыть
        </button>
      </div>
    </div>
  )
}
