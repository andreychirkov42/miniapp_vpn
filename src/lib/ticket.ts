import type { TicketStatus } from './types'

export const statusLabel: Record<TicketStatus, string> = {
  open: 'Открыто',
  answered: 'Отвечено',
  closed: 'Закрыто',
}

export const statusClass: Record<TicketStatus, string> = {
  open: 'tk-badge--open',
  answered: 'tk-badge--answered',
  closed: 'tk-badge--closed',
}

export function formatTime(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
