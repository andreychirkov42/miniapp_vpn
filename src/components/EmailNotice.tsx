import { IconShield } from '../icons'

export default function EmailNotice() {
  return (
    <div className="notice">
      <span className="notice__icon">
        <IconShield size={30} />
      </span>
      <div className="notice__text">
        <div className="notice__title">
          Привяжите Email или
          <br />
          другой способ входа
        </div>
        <div className="notice__sub">Чтобы не потерять доступ к аккаунту</div>
      </div>
      <button className="btn-purple">Привязать</button>
    </div>
  )
}
