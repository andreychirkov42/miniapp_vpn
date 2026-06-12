import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import type { ConfigResponse, Subscription } from '../lib/types'
import PlatformInstall from './PlatformInstall'
import { IconClose, IconGear } from '../icons'

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

  useEffect(() => {
    api
      .config(sub.uuid)
      .then(setCfg)
      .catch((e) => setError((e as Error).message))
  }, [sub.uuid])

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
        <div className="modal__sub">Подписка «{sub.name}». Установите приложение и подключите её.</div>

        {error && <div className="cfg-error">{error}</div>}

        {cfg && <PlatformInstall subscriptionUrl={cfg.subscription_url} />}

        <button className="btn-text" onClick={onClose}>
          Закрыть
        </button>
      </div>
    </div>
  )
}
