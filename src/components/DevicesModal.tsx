import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { haptic } from '../lib/telegram'
import type { Device, Subscription } from '../lib/types'
import { IconClose, IconDevices, IconTrash } from '../icons'

type Props = {
  sub: Subscription
  onClose: () => void
  onChanged?: () => void // обновить счётчики на главной после удаления
}

function deviceTitle(d: Device): string {
  return d.device_model || d.platform || 'Устройство'
}

function deviceSub(d: Device): string {
  const parts = [d.platform, formatDate(d.created_at)].filter(Boolean)
  return parts.join(' · ')
}

function formatDate(iso: string | null): string {
  if (!iso) return ''
  const dt = new Date(iso)
  if (Number.isNaN(dt.getTime())) return ''
  return dt.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

// Раздел «Устройства»: список HWID активной подписки + удаление каждого.
export default function DevicesModal({ sub, onClose, onChanged }: Props) {
  const [devices, setDevices] = useState<Device[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busyHwid, setBusyHwid] = useState<string | null>(null)
  const [confirmHwid, setConfirmHwid] = useState<string | null>(null)

  useEffect(() => {
    api.devices(sub.uuid)
      .then((r) => setDevices(r.devices))
      .catch((e) => setError((e as Error).message))
  }, [sub.uuid])

  const handleDelete = async (hwid: string) => {
    if (confirmHwid !== hwid) {
      setConfirmHwid(hwid) // первый тап — запрос подтверждения
      return
    }
    setBusyHwid(hwid)
    setError(null)
    try {
      const r = await api.deleteDevice(sub.uuid, hwid)
      setDevices(r.devices)
      haptic('success')
      onChanged?.()
    } catch (e) {
      setError((e as Error).message)
      haptic('error')
    } finally {
      setBusyHwid(null)
      setConfirmHwid(null)
    }
  }

  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal modal--config" onClick={(e) => e.stopPropagation()}>
        <button className="modal__close" onClick={onClose} aria-label="Закрыть">
          <IconClose size={22} />
        </button>
        <span className="modal__icon">
          <IconDevices size={34} />
        </span>
        <div className="modal__title" style={{ fontSize: 22 }}>
          Мои устройства
        </div>
        <div className="modal__sub">
          Подписка «{sub.name}». Удалите устройство, чтобы освободить слот для нового.
        </div>

        {error && <div className="cfg-error">{error}</div>}

        {devices === null && !error && <div className="dev-empty">Загрузка…</div>}

        {devices !== null && devices.length === 0 && (
          <div className="dev-empty">Пока ни одного устройства не подключено.</div>
        )}

        {devices && devices.length > 0 && (
          <div className="dev-list">
            {devices.map((d) => {
              const isConfirm = confirmHwid === d.hwid
              const isBusy = busyHwid === d.hwid
              return (
                <div key={d.hwid} className="dev-row">
                  <span className="dev-row__ic">
                    <IconDevices size={20} />
                  </span>
                  <div className="dev-row__txt">
                    <span className="dev-row__title">{deviceTitle(d)}</span>
                    {deviceSub(d) && <span className="dev-row__sub">{deviceSub(d)}</span>}
                  </div>
                  <button
                    className={`dev-row__del ${isConfirm ? 'is-confirm' : ''}`}
                    onClick={() => handleDelete(d.hwid)}
                    disabled={isBusy}
                    aria-label="Удалить устройство"
                  >
                    {isBusy ? '…' : isConfirm ? 'Удалить?' : <IconTrash size={18} />}
                  </button>
                </div>
              )
            })}
          </div>
        )}

        <button className="btn-text" onClick={onClose}>
          Закрыть
        </button>
      </div>
    </div>
  )
}
