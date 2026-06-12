import { useState } from 'react'
import { IconClose, IconGift } from '../icons'

export default function PromoModal({ onClose }: { onClose: () => void }) {
  const [code, setCode] = useState('')
  const [status, setStatus] = useState<string | null>(null)

  const apply = () => {
    if (!code.trim()) return
    // TODO backend: POST /api/promo { code } — пока промокодов нет
    setStatus('Промокод недействителен')
  }

  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal modal--config" onClick={(e) => e.stopPropagation()}>
        <button className="modal__close" onClick={onClose} aria-label="close">
          <IconClose size={22} />
        </button>
        <span className="modal__icon">
          <IconGift size={34} />
        </span>
        <div className="modal__title" style={{ fontSize: 22 }}>
          Промокод
        </div>
        <div className="modal__sub">Введите промокод, чтобы получить бонус</div>

        <input
          className="modal-input"
          placeholder="Например, ROMB2026"
          value={code}
          onChange={(e) => {
            setCode(e.target.value.toUpperCase())
            setStatus(null)
          }}
        />

        {status && <div className="cfg-error">{status}</div>}

        <button className="btn btn-primary" onClick={apply} disabled={!code.trim()}>
          Применить
        </button>
        <button className="btn-text" onClick={onClose}>
          Закрыть
        </button>
      </div>
    </div>
  )
}
