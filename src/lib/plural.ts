// Русское склонение существительных по числу.

export function plural(n: number, one: string, few: string, many: string): string {
  const m10 = n % 10
  const m100 = n % 100
  if (m10 === 1 && m100 !== 11) return one
  if (m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20)) return few
  return many
}

// "7 дней" / "1 день" / "3 дня"
export function days(n: number): string {
  return `${n} ${plural(n, 'день', 'дня', 'дней')}`
}
