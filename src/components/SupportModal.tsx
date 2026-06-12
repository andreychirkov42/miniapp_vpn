import { useState } from 'react'
import { api } from '../lib/api'
import { haptic } from '../lib/telegram'
import { IconChat, IconClose } from '../icons'

type Status = 'idle' | 'sending' | 'sent' | 'error'

export default function SupportModal({ onClose }: { onClose: () => void }) {
  const [message, setMessage] = useState('')
  const [status, setStatus] = useState<Status>('idle')
  const [error, setError] = useState<string | null>(null)

  const send = async () => {
    const text = message.trim()
    if (!text || status === 'sending') return
    setStatus('sending')
    setError(null)
    try {
      await api.support(text)
      haptic('success')
      setStatus('sent')
    } catch (e) {
      haptic('error')
      setError((e as Error).message)
      setStatus('error')
    }
  }

  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal modal--config" onClick={(e) => e.stopPropagation()}>
        <button className="modal__close" onClick={onClose} aria-label="close">
          <IconClose size={22} />
        </button>
        <span className="modal__icon">
          <IconChat size={32} />
        </span>
        <div className="modal__title" style={{ fontSize: 22 }}>
          Новое обращение
        </div>

        {status === 'sent' ? (
          <>
            <div className="modal__sub">Сообщение отправлено в поддержку. Мы ответим в Telegram.</div>
            <button className="btn btn-primary" onClick={onClose}>
              Готово
            </button>
          </>
        ) : (
          <>
            <div className="modal__sub">Опишите проблему — обращение уйдёт в поддержку</div>
            <textarea
              className="modal-input"
              rows={5}
              placeholder="Например: не подключается на iPhone"
              value={message}
              onChange={(e) => {
                setMessage(e.target.value)
                if (status === 'error') setStatus('idle')
              }}
              maxLength={2000}
            />
            {error && <div className="cfg-error">{error}</div>}
            <button
              className="btn btn-primary"
              onClick={send}
              disabled={!message.trim() || status === 'sending'}
            >
              {status === 'sending' ? 'Отправляем…' : 'Отправить'}
            </button>
            <button className="btn-text" onClick={onClose}>
              Закрыть
            </button>
          </>
        )}
      </div>
    </div>
  )
}
