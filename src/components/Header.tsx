import { IconChevronDown, IconClose, IconDots } from '../icons'

export default function Header() {
  return (
    <header className="tg-header">
      <button className="tg-pill">
        <IconClose size={20} />
        Закрыть
      </button>
      <div className="tg-pill tg-pill--icons">
        <button className="tg-pill__btn">
          <IconChevronDown size={20} />
        </button>
        <span className="tg-pill__sep" />
        <button className="tg-pill__btn">
          <IconDots size={20} />
        </button>
      </div>
    </header>
  )
}
