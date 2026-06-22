import type { KeyboardEvent } from 'react'
import { IconBars, IconBolt, IconCalendar, IconDevices, IconPlug, IconPlus, IconRocket } from '../icons'
import type { Subscription } from '../lib/types'
import { plural } from '../lib/plural'

type Props = {
  sub: Subscription | null
  onTryFree: () => void
  onAddSubscription: () => void
  onConnect: () => void
  onShowDevices: () => void
  busyTrial: boolean
  trialDays: number
}

const GB = 1024 ** 3

function daysLeft(iso: string): number {
  if (!iso) return 0
  const diff = new Date(iso).getTime() - Date.now()
  return Math.max(0, Math.ceil(diff / 86_400_000))
}

function trafficLeft(sub: Subscription): string {
  if (sub.traffic_limit_bytes === 0) return '∞'
  const left = Math.max(0, sub.traffic_limit_bytes - sub.used_traffic_bytes) / GB
  return left >= 10 || left === Math.floor(left) ? String(Math.round(left)) : left.toFixed(1)
}

// Enter/Space на плашке-кнопке (role="button") — как клик.
function onActivate(fn: () => void) {
  return (e: KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      fn()
    }
  }
}

const offerFeatures = [
  { Icon: IconBolt, label: 'Высокая\nскорость' },
  { Icon: IconDevices, label: '3\nустройства' },
  { Icon: IconBars, label: '100 ГБ\nтрафика' },
]

export default function HomeScreen({
  sub,
  onTryFree,
  onAddSubscription,
  onConnect,
  onShowDevices,
  busyTrial,
  trialDays,
}: Props) {
  const hero = (
    <section className="hero">
      <img className="hero__logo" src="/logo.png" alt="Romb" />
      <h1 className="hero__title">Быстрый и защищённый интернет</h1>
      <p className="hero__sub">Стабильное соединение и полная приватность на любом устройстве</p>
    </section>
  )

  // ---- Активная подписка: живые показатели ----
  if (sub) {
    const days = daysLeft(sub.expire_at)
    const traffic = trafficLeft(sub)
    const stats = [
      { Icon: IconCalendar, value: String(days), cap: plural(days, 'день', 'дня', 'дней') + ' осталось' },
      {
        Icon: IconDevices,
        value: sub.device_limit === 0 ? String(sub.devices_used) : `${sub.devices_used}/${sub.device_limit}`,
        cap: 'устройств',
        onClick: onShowDevices, // тап по плашке → список устройств с удалением
      },
      { Icon: IconBars, value: traffic, cap: traffic === '∞' ? 'трафик' : 'ГБ осталось' },
    ]
    return (
      <div className="home">
        {hero}
        <ul className="features">
          {stats.map(({ Icon, value, cap, onClick }) => (
            <li
              key={cap}
              className={`feature feature--stat${onClick ? ' feature--tap' : ''}`}
              {...(onClick
                ? { role: 'button', tabIndex: 0, onClick, onKeyDown: onActivate(onClick) }
                : {})}
            >
              <span className="feature__ic">
                <Icon size={22} />
              </span>
              <span className="feature__val">{value}</span>
              <span className="feature__cap">{cap}</span>
            </li>
          ))}
        </ul>
        <div className="home-cta">
          <div className="cta-block">
            <button className="btn btn-primary btn-lg" onClick={onConnect}>
              <IconPlug size={20} />
              Подключить устройство
            </button>
            <span className="cta-caption">Подписка активна до {sub.expire_text}</span>
          </div>
        </div>
      </div>
    )
  }

  // ---- Новый пользователь: оффер + триал ----
  return (
    <div className="home">
      {hero}
      <ul className="features">
        {offerFeatures.map(({ Icon, label }) => (
          <li key={label} className="feature">
            <span className="feature__ic">
              <Icon size={22} />
            </span>
            <span className="feature__label">{label}</span>
          </li>
        ))}
      </ul>
      <div className="home-cta">
        <div className="cta-block">
          <button className="btn btn-primary btn-lg" onClick={onTryFree} disabled={busyTrial}>
            <IconRocket size={22} />
            {busyTrial ? 'Активируем…' : 'Попробовать бесплатно'}
          </button>
          <span className="cta-caption">
            {trialDays} {plural(trialDays, 'день', 'дня', 'дней')} полного доступа — без карты
          </span>
        </div>
        <button className="btn btn-secondary btn-lg" onClick={onAddSubscription}>
          <IconPlus size={22} />
          У меня уже есть подписка
        </button>
      </div>
    </div>
  )
}
