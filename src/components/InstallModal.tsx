import { useState } from 'react'
import { installPlatforms } from '../data'
import { openExternal } from '../lib/telegram'
import { IconClose, IconDevices } from '../icons'

export default function InstallModal({ onClose }: { onClose: () => void }) {
  const [hint, setHint] = useState<string | null>(null)

  const pick = (url: string, label: string) => {
    if (url) openExternal(url)
    else setHint(`Ссылка для «${label}» скоро будет добавлена`)
  }

  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal modal--config" onClick={(e) => e.stopPropagation()}>
        <button className="modal__close" onClick={onClose} aria-label="close">
          <IconClose size={22} />
        </button>
        <span className="modal__icon">
          <IconDevices size={34} />
        </span>
        <div className="modal__title" style={{ fontSize: 22 }}>
          Установка приложения
        </div>
        <div className="modal__sub">Выберите устройство, на которое хотите подключить VPN</div>

        <div className="cfg-clients">
          {installPlatforms.map((p) => (
            <button key={p.id} className="cfg-client" onClick={() => pick(p.url, p.label)}>
              {p.label}
            </button>
          ))}
        </div>

        {hint && <div className="cfg-hint">{hint}</div>}

        <button className="btn-text" onClick={onClose}>
          Закрыть
        </button>
      </div>
    </div>
  )
}
