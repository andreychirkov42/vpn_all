import { closeApp, haptic } from '../lib/telegram'
import type { Tab } from './BottomNav'
import type { ProfileModal } from '../screens/ProfileScreen'
import {
  IconChat,
  IconDoc,
  IconGift,
  IconHeart,
  IconHome,
  IconLogOut,
  IconQuestion,
  IconSend,
  IconShield,
  IconWallet,
} from '../icons'

type Action = { kind: 'tab'; tab: Tab } | { kind: 'modal'; modal: ProfileModal } | { kind: 'noop' }
type Item = { id: string; label: string; Icon: typeof IconHome; action: Action }
type Section = { title: string; items: Item[] }

// Большая боковая панель как в клоне (akenai-кабинет): разделы + пункты.
// Видна только на широком экране (см. @media в index.css); в мини-аппе скрыта.
const sections: Section[] = [
  {
    title: 'Главная',
    items: [
      { id: 'home', label: 'Личный кабинет', Icon: IconHome, action: { kind: 'tab', tab: 'home' } },
      { id: 'support', label: 'Поддержка', Icon: IconChat, action: { kind: 'tab', tab: 'support' } },
      { id: 'faq', label: 'Часто задаваемые вопросы', Icon: IconQuestion, action: { kind: 'noop' } },
    ],
  },
  {
    title: 'Ссылки',
    items: [
      { id: 'channel', label: 'Канал', Icon: IconSend, action: { kind: 'noop' } },
      { id: 'privacy', label: 'Политика конфиденциальности', Icon: IconShield, action: { kind: 'noop' } },
      { id: 'terms', label: 'Пользовательское соглашение', Icon: IconDoc, action: { kind: 'noop' } },
    ],
  },
  {
    title: 'Программы',
    items: [
      { id: 'referral', label: 'Реферальная система', Icon: IconHeart, action: { kind: 'modal', modal: 'referral' } },
      { id: 'partner', label: 'Партнёрская программа', Icon: IconWallet, action: { kind: 'noop' } },
      { id: 'promo', label: 'Применить промокод', Icon: IconGift, action: { kind: 'modal', modal: 'promo' } },
    ],
  },
]

export default function Sidebar({
  active,
  onChange,
  onOpenModal,
}: {
  active: Tab
  onChange: (t: Tab) => void
  onOpenModal: (m: ProfileModal) => void
}) {
  const run = (a: Action) => {
    if (a.kind === 'tab') onChange(a.tab)
    else if (a.kind === 'modal') onOpenModal(a.modal)
    else haptic('light')
  }

  const handleExit = () => {
    haptic('light')
    closeApp()
  }

  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <img src="/logo.png" alt="Romb" />
        <span>Romb</span>
      </div>
      <div className="sidebar__scroll">
        {sections.map((section) => (
          <div key={section.title} className="sidebar__section">
            <div className="sidebar__section-title">{section.title}</div>
            {section.items.map(({ id, label, Icon, action }) => {
              const isActive = action.kind === 'tab' && action.tab === active
              return (
                <button
                  key={id}
                  className={`sidebar__btn ${isActive ? 'sidebar__btn--active' : ''}`}
                  onClick={() => run(action)}
                >
                  <Icon size={20} />
                  <span>{label}</span>
                </button>
              )
            })}
          </div>
        ))}
      </div>
      <div className="sidebar__footer">
        <button className="sidebar__btn sidebar__logout" onClick={handleExit}>
          <IconLogOut size={20} />
          <span>Выйти</span>
        </button>
      </div>
    </aside>
  )
}
