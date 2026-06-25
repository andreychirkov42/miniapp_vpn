import { useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'
import { haptic } from '../lib/telegram'
import { IconChat, IconClose, IconPlus } from '../icons'

type Status = 'idle' | 'sending' | 'sent' | 'error'

const MAX_FILE_BYTES = 5 * 1024 * 1024

export default function SupportModal({ onClose }: { onClose: () => void }) {
  const [message, setMessage] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [status, setStatus] = useState<Status>('idle')
  const [error, setError] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  // Превью выбранного файла — локальный object URL, чистим при замене/закрытии.
  useEffect(() => {
    if (!file) {
      setPreview(null)
      return
    }
    const url = URL.createObjectURL(file)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const pickFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const chosen = e.target.files?.[0] ?? null
    if (chosen && chosen.size > MAX_FILE_BYTES) {
      setError('Файл больше 5 МБ')
      setStatus('error')
      return
    }
    setFile(chosen)
    if (status === 'error') {
      setStatus('idle')
      setError(null)
    }
  }

  const send = async () => {
    const text = message.trim()
    if ((!text && !file) || status === 'sending') return
    setStatus('sending')
    setError(null)
    try {
      await api.support(text, undefined, file)
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
            <div className="modal__sub">Опишите проблему — можно приложить скриншот</div>
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

            <input
              ref={fileRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              hidden
              onChange={pickFile}
            />

            {preview ? (
              <div className="attach-preview">
                <img src={preview} alt="превью" />
                <button
                  className="attach-preview__remove"
                  onClick={() => setFile(null)}
                  aria-label="убрать"
                >
                  <IconClose size={16} />
                </button>
              </div>
            ) : (
              <button className="attach-add" onClick={() => fileRef.current?.click()}>
                <IconPlus size={18} />
                Прикрепить скриншот
              </button>
            )}

            {error && <div className="cfg-error">{error}</div>}
            <button
              className="btn btn-primary"
              onClick={send}
              disabled={(!message.trim() && !file) || status === 'sending'}
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
