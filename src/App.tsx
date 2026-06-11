import { useEffect, useState } from 'react'
import Header from './components/Header'
import BottomNav, { type Tab } from './components/BottomNav'
import TrialModal from './components/TrialModal'
import ConfigModal from './components/ConfigModal'
import InstallModal from './components/InstallModal'
import HomeScreen from './screens/HomeScreen'
import SupportScreen from './screens/SupportScreen'
import ProfileScreen from './screens/ProfileScreen'
import { useSubscriptions } from './hooks/useSubscriptions'
import { initTelegram, haptic } from './lib/telegram'
import type { Subscription } from './lib/types'

export default function App() {
  const [tab, setTab] = useState<Tab>('home')
  const { subs, loading, error, reload, activateTrial } = useSubscriptions()
  const [trialSuccess, setTrialSuccess] = useState(false)
  const [showInstall, setShowInstall] = useState(false)
  const [configSub, setConfigSub] = useState<Subscription | null>(null)
  const [busyTrial, setBusyTrial] = useState(false)

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
      <Header />

      <main className={`content ${tab === 'home' ? 'content--center' : ''}`}>
        {loading && <CenterMsg text="Загрузка…" />}
        {!loading && error && <CenterMsg text={`Ошибка: ${error}`} onRetry={reload} />}
        {!loading && !error && tab === 'home' && (
          <HomeScreen
            onTryFree={handleTryFree}
            onAddSubscription={handleAddSubscription}
            busyTrial={busyTrial}
          />
        )}
        {!loading && !error && tab === 'support' && <SupportScreen />}
        {!loading && !error && tab === 'profile' && <ProfileScreen />}
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
      {showInstall && <InstallModal onClose={() => setShowInstall(false)} />}
      {configSub && (
        <ConfigModal sub={configSub} title="Добавить подписку" onClose={() => setConfigSub(null)} />
      )}
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
