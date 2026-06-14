import { useEffect, useState } from 'react'
import BottomNav, { type Tab } from './components/BottomNav'
import TrialModal from './components/TrialModal'
import ConfigModal from './components/ConfigModal'
import DevicesModal from './components/DevicesModal'
import InstallModal from './components/InstallModal'
import HomeScreen from './screens/HomeScreen'
import SupportScreen from './screens/SupportScreen'
import ProfileScreen, { type ProfileModal } from './screens/ProfileScreen'
import PaymentsModal from './components/PaymentsModal'
import { useSubscriptions } from './hooks/useSubscriptions'
import { initTelegram, haptic, openBot, getInitData } from './lib/telegram'
import { BOT_USERNAME } from './data'
import { IconRocket } from './icons'
import type { Subscription } from './lib/types'

// Нет контекста Telegram = нечем авторизоваться (мини-апп открыт вне Telegram
// либо запущен так, что initData не пришёл и нет сохранённого). Только в этом
// случае показываем экран «Откройте через бота» — иначе это сетевая/панельная
// ошибка, и нужно показать её текст с кнопкой «Повторить», а не тупик.
function isNoTelegramContext(): boolean {
  return getInitData() === ''
}

export default function App() {
  const [tab, setTab] = useState<Tab>('home')
  const { subs, isAdmin, loading, error, reload, activateTrial } = useSubscriptions()
  const [trialSuccess, setTrialSuccess] = useState(false)
  const [showInstall, setShowInstall] = useState(false)
  const [configSub, setConfigSub] = useState<Subscription | null>(null)
  const [devicesSub, setDevicesSub] = useState<Subscription | null>(null)
  const [busyTrial, setBusyTrial] = useState(false)
  const [profileModal, setProfileModal] = useState<ProfileModal | null>(null)

  useEffect(() => {
    initTelegram()
  }, [])

  // «Попробовать бесплатно» → активировать триал → экран успеха → установка
  const handleTryFree = async () => {
    setBusyTrial(true)
    try {
      await activateTrial()
      haptic('success')
      setTrialSuccess(true)
    } catch {
      haptic('error')
    } finally {
      setBusyTrial(false)
    }
  }

  // «Добавить подписку» → подписка из Remnawave → открыть в клиенте (deeplink)
  const handleAddSubscription = () => {
    if (subs.length > 0) {
      setConfigSub(subs[0])
    } else {
      void handleTryFree()
    }
  }

  return (
    <div className="app">
      <main className={`content ${tab === 'home' ? 'content--center' : ''}`}>
        {loading && <CenterMsg text="Загрузка…" />}
        {!loading && error &&
          (isNoTelegramContext() ? (
            <NeedTelegram />
          ) : (
            <CenterMsg text={`Ошибка: ${error}`} onRetry={reload} />
          ))}
        {!loading && !error && tab === 'home' && (
          <HomeScreen
            sub={subs.find((s) => !s.expired) ?? null}
            onTryFree={handleTryFree}
            onAddSubscription={handleAddSubscription}
            onConnect={() => setConfigSub(subs.find((s) => !s.expired) ?? subs[0] ?? null)}
            onShowDevices={() => setDevicesSub(subs.find((s) => !s.expired) ?? subs[0] ?? null)}
            busyTrial={busyTrial}
          />
        )}
        {!loading && !error && tab === 'support' && <SupportScreen isAdmin={isAdmin} />}
        {!loading && !error && tab === 'profile' && <ProfileScreen onOpenModal={setProfileModal} />}
      </main>

      <BottomNav active={tab} onChange={setTab} />

      {trialSuccess && (
        <TrialModal
          busy={false}
          onConnect={() => {
            setTrialSuccess(false)
            setShowInstall(true)
          }}
          onClose={() => setTrialSuccess(false)}
        />
      )}
      {showInstall && (
        <InstallModal
          subscriptionUrl={subs[0]?.subscription_url}
          onClose={() => setShowInstall(false)}
        />
      )}
      {configSub && (
        <ConfigModal sub={configSub} title="Добавить подписку" onClose={() => setConfigSub(null)} />
      )}
      {devicesSub && (
        <DevicesModal
          sub={devicesSub}
          onClose={() => setDevicesSub(null)}
          onChanged={reload}
        />
      )}
      {profileModal === 'payments' && <PaymentsModal onClose={() => setProfileModal(null)} />}
    </div>
  )
}

// Экран при запуске вне Telegram: мини-апп получает подписанный initData только
// внутри Telegram, поэтому просим открыть кабинет через бота.
function NeedTelegram() {
  return (
    <div className="center-msg need-tg">
      <span className="need-tg__ic">
        <IconRocket size={40} />
      </span>
      <h2 className="need-tg__title">Откройте через Telegram</h2>
      <p className="need-tg__text">
        Кабинет работает внутри Telegram. Запустите его заново через бота — по кнопке
        «Кабинет» или меню-кнопке.
      </p>
      <button className="btn btn-primary btn-lg" onClick={() => openBot(BOT_USERNAME)}>
        Открыть бота
      </button>
    </div>
  )
}

function CenterMsg({ text, onRetry }: { text: string; onRetry?: () => void }) {
  return (
    <div className="center-msg">
      <span>{text}</span>
      {onRetry && (
        <button className="btn-text" onClick={onRetry}>
          Повторить
        </button>
      )}
    </div>
  )
}
