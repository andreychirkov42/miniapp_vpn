import { profileList } from '../data'
import { haptic } from '../lib/telegram'
import {
  IconCard,
  IconChevronRight,
  IconDoc,
  IconGift,
  IconHeart,
  IconQuestion,
  IconRss,
  IconSend,
  IconShield,
  IconUser,
  IconWallet,
} from '../icons'

const itemIcon = {
  gift: IconGift,
  rss: IconRss,
  send: IconSend,
  shield: IconShield,
  doc: IconDoc,
  heart: IconHeart,
  wallet: IconWallet,
  export: IconShield,
  question: IconQuestion,
  login: IconShield,
  card: IconCard,
}

export type ProfileModal = 'promo' | 'referral' | 'payments'

export default function ProfileScreen({ onOpenModal }: { onOpenModal: (m: ProfileModal) => void }) {
  const handle = (id: string) => {
    if (id === 'promo' || id === 'referral' || id === 'payments') onOpenModal(id)
    else haptic('light')
  }

  return (
    <div className="profile">
      <div className="profile-head">
        <span className="profile-head__avatar">
          <IconUser size={30} />
        </span>
        <div className="profile-head__txt">
          <div className="profile-head__name">Профиль</div>
          <div className="profile-head__sub">Управление аккаунтом и бонусами</div>
        </div>
      </div>

      <div className="group__card">
        {profileList.map((item) => {
          const Icon = itemIcon[item.icon]
          return (
            <button key={item.id} className="group-row" onClick={() => handle(item.id)}>
              <span className="group-row__ic">
                <Icon size={22} />
              </span>
              <span className="group-row__title">{item.title}</span>
              <span className="group-row__chev">
                <IconChevronRight size={20} />
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
