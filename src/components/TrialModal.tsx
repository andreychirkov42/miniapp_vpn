import { IconPlug } from '../icons'
import { days } from '../lib/plural'

export default function TrialModal({
  busy,
  trialDays,
  onConnect,
  onClose,
}: {
  busy: boolean
  trialDays: number
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
          {days(trialDays)} полного доступа — подключите устройство, чтобы начать
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
