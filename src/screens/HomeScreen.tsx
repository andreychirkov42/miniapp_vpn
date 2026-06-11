import { IconPlus, IconRocket } from '../icons'

type Props = {
  onTryFree: () => void
  onAddSubscription: () => void
  busyTrial: boolean
}

export default function HomeScreen({ onTryFree, onAddSubscription, busyTrial }: Props) {
  return (
    <div className="home-actions">
      <div className="home-cta">
        <div className="cta-block">
          <button className="btn btn-primary btn-lg" onClick={onTryFree} disabled={busyTrial}>
            <IconRocket size={22} />
            {busyTrial ? 'Активируем…' : 'Попробовать бесплатно'}
          </button>
          <span className="cta-caption">3 дня полного доступа — без карты</span>
        </div>

        <div className="cta-block">
          <button className="btn btn-secondary btn-lg" onClick={onAddSubscription}>
            <IconPlus size={22} />
            Добавить подписку
          </button>
          <span className="cta-caption">Если подписка уже есть — подключить на устройство</span>
        </div>
      </div>
    </div>
  )
}
