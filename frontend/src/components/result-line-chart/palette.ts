export const CHART_COLORS = [
  '#2f80ed', // синий
  '#eb5757', // красный
  '#27ae60', // зелёный
  '#f2994a', // оранжевый
  '#9b51e0', // фиолетовый
  '#2d9cdb', // голубой
  '#b8860b', // тёмно-золотой
  '#6b7280', // серый
] as const

export function colorForIndex(i: number): string {
  return CHART_COLORS[i % CHART_COLORS.length]
}
