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

        charts: [
          {
            title: 'Доля перелива от высоты стенки',
            datasets: [
              {
                data: [
                  { x: 0.7, y: 10 },
                  { x: 0.96, y: 0 },
                  { x: 1.1, y: 0 },
                ],
                label: 'I = 3.0 м',
              },
              {
                data: [
                  [0.7, 12],
                  [0.98, 0],
                  [1.1, 0],
                ],
                label: 'I = 2.4 м',
              },
            ],
          },
        ],
      })
    }, DELAY_MS)
  })
}
