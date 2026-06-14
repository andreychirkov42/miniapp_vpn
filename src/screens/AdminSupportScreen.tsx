import { useState } from 'react'
import { api } from '../lib/api'
import { usePolling } from '../hooks/usePolling'
import TicketList from '../components/TicketList'
import TicketThread from '../components/TicketThread'
import type { TicketListResponse } from '../lib/types'
import { IconChat } from '../icons'

const POLL_MS = 8000

// Раздел «Заявки» для админа: лента всех обращений (активные/все) + диалог.
export default function AdminSupportScreen() {
  const [onlyActive, setOnlyActive] = useState(true)
  const [openId, setOpenId] = useState<number | null>(null)

  const { data, loading, error } = usePolling<TicketListResponse>(
    () => api.admin.tickets(onlyActive),
    POLL_MS,
    openId === null, // пока открыт тред — ленту не поллим
    [onlyActive], // смена сегмента «Активные/Все» → немедленный перезапрос
  )

  const tickets = data?.tickets ?? []

  if (openId !== null) {
    return <TicketThread ticketId={openId} role="admin" onClose={() => setOpenId(null)} />
  }

  return (
    <div>
      <div className="segmented">
        <button className={onlyActive ? 'active' : ''} onClick={() => setOnlyActive(true)}>
          Активные
        </button>
        <button className={!onlyActive ? 'active' : ''} onClick={() => setOnlyActive(false)}>
          Все
        </button>
      </div>

      {error && <div className="cfg-error">{error}</div>}

      {tickets.length > 0 ? (
        <TicketList tickets={tickets} showAuthor onOpen={setOpenId} />
      ) : (
        !loading && (
          <div className="empty">
            <IconChat size={64} strokeWidth={1.5} />
            <span>{onlyActive ? 'Нет активных заявок' : 'Заявок пока нет'}</span>
          </div>
        )
      )}
    </div>
  )
}
