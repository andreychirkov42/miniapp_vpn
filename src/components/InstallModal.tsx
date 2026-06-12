import PlatformInstall from './PlatformInstall'
import { IconClose, IconDevices } from '../icons'

export default function InstallModal({
  subscriptionUrl,
  onClose,
}: {
  subscriptionUrl?: string
  onClose: () => void
}) {
  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal modal--config" onClick={(e) => e.stopPropagation()}>
        <button className="modal__close" onClick={onClose} aria-label="close">
          <IconClose size={22} />
        </button>
        <span className="modal__icon">
          <IconDevices size={34} />
        </span>
        <div className="modal__title" style={{ fontSize: 22 }}>
          Установка приложения
        </div>
        <div className="modal__sub">Мы определили вашу платформу — установите приложение для неё</div>

        <PlatformInstall subscriptionUrl={subscriptionUrl} />

        <button className="btn-text" onClick={onClose}>
          Закрыть
        </button>
      </div>
    </div>
  )
}
