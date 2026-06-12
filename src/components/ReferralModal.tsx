import { useState } from 'react'
import { BOT_USERNAME, REFERRAL_BONUS_DAYS } from '../data'
import { getUserId, shareToTelegram } from '../lib/telegram'
import { IconClose, IconHeart } from '../icons'

export default function ReferralModal({ onClose }: { onClose: () => void }) {
  const id = getUserId() ?? 0
  const link = `https://t.me/${BOT_USERNAME}?start=ref${id}`
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(link)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal modal--config" onClick={(e) => e.stopPropagation()}>
        <button className="modal__close" onClick={onClose} aria-label="close">
          <IconClose size={22} />
        </button>
        <span className="modal__icon">
          <IconHeart size={34} />
        </span>
        <div className="modal__title" style={{ fontSize: 22 }}>
          Реферальная система
        </div>
        <div className="modal__sub">
          Пригласите друга по своей ссылке. После его первой оплаты вы получите{' '}
          <b>{REFERRAL_BONUS_DAYS} дней бесплатно</b>.
        </div>

        <button className="cfg-url" onClick={copy}>
          <span>{link}</span>
          <b>{copied ? 'Скопировано' : 'Копировать'}</b>
        </button>

        <button
          className="btn btn-primary"
          onClick={() => shareToTelegram(link, 'Подключайся к Romb — быстрый и защищённый интернет')}
        >
          Поделиться ссылкой
        </button>
        <button className="btn-text" onClick={onClose}>
          Закрыть
        </button>
      </div>
    </div>
  )
}
