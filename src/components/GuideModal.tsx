import { INSTALL_GUIDE_DESKTOP_URL, INSTALL_GUIDE_IOS_URL } from '../data'
import { haptic, openExternal } from '../lib/telegram'
import { IconChevronRight, IconClose, IconMonitor, IconPhone, IconQuestion } from '../icons'

type GuideOption = {
  url: string
  title: string
  sub: string
  Icon: typeof IconPhone
}

const options: GuideOption[] = [
  {
    url: INSTALL_GUIDE_IOS_URL,
    title: 'iPhone / iPad',
    sub: 'Установка на iOS',
    Icon: IconPhone,
  },
  {
    url: INSTALL_GUIDE_DESKTOP_URL,
    title: 'Компьютер и Android',
    sub: 'Windows · macOS · Android — через FLClash',
    Icon: IconMonitor,
  },
]

export default function GuideModal({ onClose }: { onClose: () => void }) {
  const open = (url: string) => {
    haptic('light')
    openExternal(url)
    onClose()
  }

  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal modal--config" onClick={(e) => e.stopPropagation()}>
        <button className="modal__close" onClick={onClose} aria-label="close">
          <IconClose size={22} />
        </button>
        <span className="modal__icon">
          <IconQuestion size={32} />
        </span>
        <div className="modal__title" style={{ fontSize: 22 }}>
          Инструкция по установке
        </div>
        <div className="modal__sub">Выберите ваше устройство</div>

        <div className="guide-options">
          {options.map(({ url, title, sub, Icon }) => (
            <button key={url} type="button" className="guide-option" onClick={() => open(url)}>
              <span className="guide-option__ic">
                <Icon size={26} />
              </span>
              <span className="guide-option__txt">
                <span className="guide-option__title">{title}</span>
                <span className="guide-option__sub">{sub}</span>
              </span>
              <span className="guide-option__chev">
                <IconChevronRight size={20} />
              </span>
            </button>
          ))}
        </div>

        <button className="btn-text" onClick={onClose}>
          Закрыть
        </button>
      </div>
    </div>
  )
}
