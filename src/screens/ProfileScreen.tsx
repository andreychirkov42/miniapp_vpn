import { profileItems } from '../data'
import {
  IconCard,
  IconChevronRight,
  IconDoc,
  IconExport,
  IconGift,
  IconHeart,
  IconQuestion,
  IconRss,
  IconSend,
  IconShield,
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
  export: IconExport,
  question: IconQuestion,
  login: IconShield,
  card: IconCard,
}

export default function ProfileScreen() {
  return (
    <div className="list">
      {profileItems.map((item) => {
        const Icon = itemIcon[item.icon]
        return (
          <button key={item.id} className="list-row">
            <span className="list-row__ic">
              <Icon size={24} />
            </span>
            <span className="list-row__title">{item.title}</span>
            <span className="list-row__chev">
              <IconChevronRight size={22} />
            </span>
          </button>
        )
      })}
    </div>
  )
}
