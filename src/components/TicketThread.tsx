import { useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'
import { haptic } from '../lib/telegram'
import { formatTime, statusClass, statusLabel } from '../lib/ticket'
import { usePolling } from '../hooks/usePolling'
import type { TicketDetail } from '../lib/types'
import { IconChevronLeft, IconClose, IconPlus, IconSend } from '../icons'
import AttachmentImage from './AttachmentImage'

const POLL_MS = 6000
const MAX_FILE_BYTES = 5 * 1024 * 1024

type Props = {
  ticketId: number
  role: 'user' | 'admin'
  onClose: () => void
}

// Переписка по одному обращению. Юзер и админ используют один компонент —
// отличаются способом отправки (support vs admin.reply) и кнопкой «Закрыть».
export default function TicketThread({ ticketId, role, onClose }: Props) {
  const fetcher = role === 'admin' ? () => api.admin.ticket(ticketId) : () => api.myTicket(ticketId)
  const { data, error, refresh } = usePolling<TicketDetail>(fetcher, POLL_MS)

  const [draft, setDraft] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [lightbox, setLightbox] = useState<string | null>(null)
  const [sending, setSending] = useState(false)
  const bodyRef = useRef<HTMLDivElement>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const messages = data?.messages ?? []
  const isClosed = data?.status === 'closed'

  // Пока открыт тред — прячем нижнюю навигацию мини-аппа (иначе её плавающая
  // «таблетка» накладывается на поле ввода).
  useEffect(() => {
    document.body.classList.add('thread-open')
    return () => document.body.classList.remove('thread-open')
  }, [])

  // Автопрокрутка вниз при появлении новых сообщений.
  useEffect(() => {
    const el = bodyRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages.length])

  // Локальное превью выбранного вложения.
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
      haptic('error')
      return
    }
    setFile(chosen)
  }

  const send = async () => {
    const text = draft.trim()
    if ((!text && !file) || sending) return
    setSending(true)
    try {
      if (role === 'admin') {
        await api.admin.reply(ticketId, text, file)
      } else {
        await api.support(text, ticketId, file)
      }
      haptic('success')
      setDraft('')
      setFile(null)
      await refresh()
    } catch {
      haptic('error')
    } finally {
      setSending(false)
    }
  }

  const closeTicket = async () => {
    if (sending) return
    setSending(true)
    try {
      await api.admin.close(ticketId)
      haptic('success')
      await refresh()
    } catch {
      haptic('error')
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="thread">
      <header className="thread__head">
        <button className="thread__back" onClick={onClose} aria-label="назад">
          <IconChevronLeft size={24} />
        </button>
        <span className="thread__title">Обращение #{ticketId}</span>
        {data && (
          <span className={`tk-badge ${statusClass[data.status]}`}>{statusLabel[data.status]}</span>
        )}
        {role === 'admin' && !isClosed && (
          <button className="btn-text" onClick={closeTicket} disabled={sending}>
            Закрыть
          </button>
        )}
      </header>

      <div className="thread__body" ref={bodyRef}>
        {error && <div className="cfg-error">{error}</div>}
        {messages.map((m) => {
          // Сторона пузыря — с точки зрения смотрящего: своё сообщение справа
          // (зелёное), чужое слева. Для админа «своё» — это ответы админа.
          const isMine = m.author === role
          return (
            <div key={m.id} className={`bubble ${isMine ? 'bubble--user' : 'bubble--admin'}`}>
              {m.attachment_url && (
                <AttachmentImage url={m.attachment_url} onOpen={setLightbox} />
              )}
              {m.text && <span className="bubble__text">{m.text}</span>}
              <span className="bubble__time">{formatTime(m.created_at)}</span>
            </div>
          )
        })}
      </div>

      {isClosed ? (
        <div className="thread__closed">Обращение закрыто</div>
      ) : (
        <div className="thread__composer-wrap">
          {preview && (
            <div className="attach-preview attach-preview--composer">
              <img src={preview} alt="превью" />
              <button
                className="attach-preview__remove"
                onClick={() => setFile(null)}
                aria-label="убрать"
              >
                <IconClose size={16} />
              </button>
            </div>
          )}
          <div className="thread__composer">
            <input
              ref={fileRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              hidden
              onChange={pickFile}
            />
            <button
              className="thread__attach"
              onClick={() => fileRef.current?.click()}
              aria-label="прикрепить"
            >
              <IconPlus size={20} />
            </button>
            <textarea
              rows={1}
              placeholder={role === 'admin' ? 'Ответ пользователю…' : 'Сообщение…'}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              maxLength={2000}
            />
            <button
              className="thread__send"
              onClick={send}
              disabled={(!draft.trim() && !file) || sending}
            >
              <IconSend size={20} />
            </button>
          </div>
        </div>
      )}

      {lightbox && (
        <div className="lightbox" onClick={() => setLightbox(null)}>
          <img src={lightbox} alt="вложение" />
        </div>
      )}
    </div>
  )
}
