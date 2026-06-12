import { useState } from 'react'
import { supportActions } from '../data'
import { haptic } from '../lib/telegram'
import SupportModal from '../components/SupportModal'
import { IconChat, IconChevronRight, IconDevices, IconPlus, IconQuestion } from '../icons'

const actionIcon = {
  plus: IconPlus,
  question: IconQuestion,
  devices: IconDevices,
}

export default function SupportScreen() {
  const [tab, setTab] = useState<'open' | 'history'>('open')
  const [showSupport, setShowSupport] = useState(false)

  // Обращение пишется и отправляется прямо в мини-аппе (бэкенд доставит в поддержку).
  const handleAction = () => {
    haptic('light')
    setShowSupport(true)
  }

  return (
    <div>
      <div className="menu-card">
        {supportActions.map((a) => {
          const Icon = actionIcon[a.icon]
          return (
            <button key={a.id} className="menu-row" onClick={handleAction}>
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

      <div className="empty">
        <IconChat size={64} strokeWidth={1.5} />
        <span>{tab === 'open' ? 'Нет открытых обращений' : 'История обращений пуста'}</span>
      </div>

      {showSupport && <SupportModal onClose={() => setShowSupport(false)} />}
    </div>
  )
}
