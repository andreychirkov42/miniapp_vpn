import { useState } from 'react'
import { copyToClipboard, haptic } from '../lib/telegram'
import { IconCard, IconCheck, IconClose, IconDoc } from '../icons'

// Реквизиты статичные — при смене карты/тарифа править здесь.
const CARD_NUMBER = '4177 4901 8201 5059'
const RECIPIENT = 'Мирошников В.'

export default function HowToPayModal({ onClose }: { onClose: () => void }) {
  const [copied, setCopied] = useState(false)

  const copyCard = () => {
    // В буфер кладём номер без пробелов — так удобнее вставлять в банковское поле.
    const ok = copyToClipboard(CARD_NUMBER.replace(/\s/g, ''))
    haptic(ok ? 'success' : 'error')
    if (ok) {
      setCopied(true)
      setTimeout(() => setCopied(false), 1800)
    }
  }

  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal modal--config" onClick={(e) => e.stopPropagation()}>
        <button className="modal__close" onClick={onClose} aria-label="close">
          <IconClose size={22} />
        </button>
        <span className="modal__icon">
          <IconCard size={32} />
        </span>
        <div className="modal__title" style={{ fontSize: 22 }}>
          Как оплатить
        </div>
        <div className="modal__sub">Продление «Сервер Киргизия»</div>

        <div className="pay-info">
          <div className="pay-info__row">
            <span className="pay-info__label">Срок действия</span>
            <span className="pay-info__value">6 месяцев</span>
          </div>
          <div className="pay-info__row">
            <span className="pay-info__label">Стоимость</span>
            <span className="pay-info__value">$19 (1 450 ₽)</span>
          </div>
          <div className="pay-info__row">
            <span className="pay-info__label">Способ оплаты</span>
            <span className="pay-info__value">Перевод через приложение МБАНК на карту МБАНК</span>
          </div>
        </div>

        <div className="pay-steps__title">Инструкция</div>
        <ol className="pay-steps">
          <li>Откройте приложение МБАНК.</li>
          <li>Перейдите в раздел «Переводы» → «По номеру карты».</li>
          <li>
            Укажите реквизиты перевода:
            <div className="pay-req">
              <button
                type="button"
                className="pay-req__row pay-req__row--copy"
                onClick={copyCard}
                aria-label="Скопировать номер карты"
              >
                <span className="pay-req__label">Номер карты</span>
                <span className="pay-req__value">
                  {CARD_NUMBER}
                  <span className="pay-req__copy">
                    {copied ? <IconCheck size={15} /> : <IconDoc size={15} />}
                    {copied ? 'Скопировано' : 'Копировать'}
                  </span>
                </span>
              </button>
              <div className="pay-req__row">
                <span className="pay-req__label">Валюта</span>
                <span className="pay-req__value">USD</span>
              </div>
              <div className="pay-req__row">
                <span className="pay-req__label">Размер перевода</span>
                <span className="pay-req__value">$19</span>
              </div>
              <div className="pay-req__row">
                <span className="pay-req__label">Получатель</span>
                <span className="pay-req__value">{RECIPIENT}</span>
              </div>
            </div>
          </li>
          <li>
            Нажмите «Перевести» и отправьте скриншот чека в поддержку прямо в приложении
            (раздел «Поддержка» → «Новое обращение»).
          </li>
        </ol>

        <button className="btn-text" onClick={onClose}>
          Закрыть
        </button>
      </div>
    </div>
  )
}
