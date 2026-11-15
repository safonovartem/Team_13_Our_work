// src/mock-api.ts
import type { CalculationResult, FormValues } from './types'

const DELAY_MS = 600

export function calculate(form: FormValues): Promise<CalculationResult> {
  // имитация сети
  return new Promise((resolve) => {
    setTimeout(() => {
      // тут можно ветвиться по form.fillLevel и т.п.
      resolve({
        variants: [
          {
            id: 'no-canopy',
            title: 'Без козырька',
            items: [
              { title: 'Доля перелива', value: '31%' },
              { title: 'Стоимость', value: '12 млн ₽' },
              { title: 'Безопасность', value: 'Низкая' },
              { title: 'Реализуемость', value: 'Высокая' },
            ],
          },
          {
            id: 'gvk',
            title: 'С ГВК',
            isImportant: true,
            items: [
              { title: 'Доля перелива', value: '12%' },
              { title: 'Стоимость', value: '16 млн ₽' },
              { title: 'Безопасность', value: 'Высокая' },
              { title: 'Реализуемость', value: 'Хорошая' },
            ],
          },
          {
            id: 'nvk',
            title: 'С НВК',
            items: [
              { title: 'Доля перелива', value: '9%' },
              { title: 'Стоимость', value: '21 млн ₽' },
              { title: 'Безопасность', value: 'Высокая' },
              { title: 'Реализуемость', value: 'Средняя' },
            ],
          },
        ],
      })
    }, DELAY_MS)
  })
}
