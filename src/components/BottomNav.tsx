import { IconChat, IconHome, IconUser } from '../icons'

export type Tab = 'home' | 'support' | 'profile'

const tabs: { id: Tab; Icon: typeof IconHome }[] = [
  { id: 'home', Icon: IconHome },
  { id: 'support', Icon: IconChat },
  { id: 'profile', Icon: IconUser },
]

export default function BottomNav({
  active,
  onChange,
}: {
  active: Tab
  onChange: (t: Tab) => void
}) {
  return (
    <nav className="nav">
      <div className="nav__pill">
        {tabs.map(({ id, Icon }) => (
          <button
            key={id}
            className={`nav__btn ${active === id ? 'nav__btn--active' : ''}`}
            onClick={() => onChange(id)}
            aria-label={id}
          >
            <Icon size={26} />
          </button>
        ))}
      </div>
    </nav>
  )
}
