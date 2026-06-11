import { IconPlug } from '../icons'

export default function TrialModal({
  busy,
  onConnect,
  onClose,
}: {
  busy: boolean
  onConnect: () => void
  onClose: () => void
}) {
  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <span className="modal__icon">
          <IconPlug size={38} />
        </span>
        <div className="modal__title">
          Пробный период
          <br />
          активирован!
        </div>
        <div className="modal__sub">
          3 дней доступа — подключите устройство, чтобы начать
        </div>
        <button className="btn btn-primary" onClick={onConnect} disabled={busy}>
          {busy ? 'Подключаем…' : 'Подключить устройство'}
        </button>
        <button className="btn-text" onClick={onClose} disabled={busy}>
          Позже
        </button>
      </div>
    </div>
  )
}
