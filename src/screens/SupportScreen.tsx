import { useState } from 'react'
import { supportActions, type SupportAction } from '../data'
import { haptic } from '../lib/telegram'
import { usePolling } from '../hooks/usePolling'
import { api } from '../lib/api'
import GuideModal from '../components/GuideModal'
import SupportModal from '../components/SupportModal'
import TicketList from '../components/TicketList'
import TicketThread from '../components/TicketThread'
import AdminSupportScreen from './AdminSupportScreen'
import type { TicketListResponse } from '../lib/types'
import { IconChat, IconChevronRight, IconDevices, IconPlus, IconQuestion } from '../icons'

const POLL_MS = 8000

const actionIcon = {
  plus: IconPlus,
  question: IconQuestion,
  devices: IconDevices,
}

export default function SupportScreen({ isAdmin = false }: { isAdmin?: boolean }) {
  const [scope, setScope] = useState<'mine' | 'admin'>('mine')
  const [tab, setTab] = useState<'open' | 'history'>('open')
  const [showSupport, setShowSupport] = useState(false)
  const [showGuide, setShowGuide] = useState(false)
  const [openId, setOpenId] = useState<number | null>(null)

  const { data, loading, error, refresh } = usePolling<TicketListResponse>(
    () => api.myTickets(),
    POLL_MS,
    scope === 'mine' && openId === null,
  )

  const tickets = data?.tickets ?? []
  const active = tickets.filter((t) => t.status !== 'closed')
  const history = tickets.filter((t) => t.status === 'closed')
  const shown = tab === 'open' ? active : history

  const handleAction = (action: SupportAction) => {
    haptic('light')
    if (action.id === 'guide') {
      setShowGuide(true)
      return
    }
    setShowSupport(true)
  }

  // Открытый тред (юзер) — поверх всего.
  if (scope === 'mine' && openId !== null) {
    return <TicketThread ticketId={openId} role="user" onClose={() => setOpenId(null)} />
  }

  return (
    <div>
      {isAdmin && (
        <div className="segmented">
          <button className={scope === 'mine' ? 'active' : ''} onClick={() => setScope('mine')}>
            Мои обращения
          </button>
          <button className={scope === 'admin' ? 'active' : ''} onClick={() => setScope('admin')}>
            Заявки
          </button>
        </div>
      )}

      {scope === 'admin' ? (
        <AdminSupportScreen />
      ) : (
        <>
          <div className="menu-card">
            {supportActions.map((a) => {
              const Icon = actionIcon[a.icon]
              return (
                <button key={a.id} className="menu-row" onClick={() => handleAction(a)}>
                  <span className="menu-row__ic">
                    <Icon size={24} />
                  </span>
                  <span className="menu-row__txt">
                    <div className="menu-row__title">{a.title}</div>
                    <div className="menu-row__sub">{a.sub}</div>
                  </span>
                  <span className="menu-row__chev">
                    <IconChevronRight size={20} />
                  </span>
                </button>
              )
            })}
          </div>

          <div className="segmented">
            <button className={tab === 'open' ? 'active' : ''} onClick={() => setTab('open')}>
              Открытые
            </button>
            <button className={tab === 'history' ? 'active' : ''} onClick={() => setTab('history')}>
              История
            </button>
          </div>

          {error && <div className="cfg-error">{error}</div>}

          {shown.length > 0 ? (
            <TicketList tickets={shown} onOpen={setOpenId} />
          ) : (
            !loading && (
              <div className="empty">
                <IconChat size={64} strokeWidth={1.5} />
                <span>{tab === 'open' ? 'Нет открытых обращений' : 'История обращений пуста'}</span>
              </div>
            )
          )}
        </>
      )}

      {showSupport && (
        <SupportModal
          onClose={() => {
            setShowSupport(false)
            void refresh()
          }}
        />
      )}

      {showGuide && <GuideModal onClose={() => setShowGuide(false)} />}
    </div>
  )
}
