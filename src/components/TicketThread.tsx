import { useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'
import { haptic } from '../lib/telegram'
import { formatTime, statusClass, statusLabel } from '../lib/ticket'
import { usePolling } from '../hooks/usePolling'
import type { TicketDetail } from '../lib/types'
import { IconChevronLeft, IconSend } from '../icons'

const POLL_MS = 6000

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
  const [sending, setSending] = useState(false)
  const bodyRef = useRef<HTMLDivElement>(null)

  const messages = data?.messages ?? []
  const isClosed = data?.status === 'closed'

  // Автопрокрутка вниз при появлении новых сообщений.
  useEffect(() => {
    const el = bodyRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages.length])

  const send = async () => {
    const text = draft.trim()
    if (!text || sending) return
    setSending(true)
    try {
      if (role === 'admin') {
        await api.admin.reply(ticketId, text)
      } else {
        await api.support(text, ticketId)
      }
      haptic('success')
      setDraft('')
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
        {messages.map((m) => (
          <div key={m.id} className={`bubble ${m.author === 'user' ? 'bubble--user' : 'bubble--admin'}`}>
            {m.text}
            <span className="bubble__time">{formatTime(m.created_at)}</span>
          </div>
        ))}
      </div>

      {isClosed ? (
        <div className="thread__closed">Обращение закрыто</div>
      ) : (
        <div className="thread__composer">
          <textarea
            rows={1}
            placeholder={role === 'admin' ? 'Ответ пользователю…' : 'Сообщение…'}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            maxLength={2000}
          />
          <button className="thread__send" onClick={send} disabled={!draft.trim() || sending}>
            <IconSend size={20} />
          </button>
        </div>
      )}
    </div>
  )
}
