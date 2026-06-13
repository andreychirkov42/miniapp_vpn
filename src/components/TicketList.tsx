import { statusClass, statusLabel } from '../lib/ticket'
import type { Ticket } from '../lib/types'

type Props = {
  tickets: Ticket[]
  showAuthor?: boolean // для админа — показать, кто автор
  onOpen: (id: number) => void
}

export default function TicketList({ tickets, showAuthor = false, onOpen }: Props) {
  return (
    <div className="ticket-list">
      {tickets.map((t) => {
        const who = t.first_name || (t.username ? `@${t.username}` : `id ${t.user_telegram_id}`)
        const prefix = t.last_author === 'admin' ? 'Поддержка: ' : ''
        return (
          <button key={t.id} className="ticket-row" onClick={() => onOpen(t.id)}>
            <div className="ticket-row__top">
              <span className="ticket-row__id">Обращение #{t.id}</span>
              <span className={`tk-badge ${statusClass[t.status]}`}>{statusLabel[t.status]}</span>
            </div>
            {showAuthor && <span className="ticket-row__who">{who}</span>}
            {t.last_message && (
              <span className="ticket-row__preview">
                {prefix}
                {t.last_message}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
