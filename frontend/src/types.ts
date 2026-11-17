import { ChartDataset, Point } from 'chart.js'

// Результаты

export type ResultItem = {
  title: string
  value: string
}

export type ResultBlock = {
  id: string
  title: string
  isImportant?: boolean
  items: ResultItem[]
}

export type ChartBlock = {
  title: string
  datasets: ChartDataset<'line', ([number, number] | Point | null)[]>[]
}

export type CalculationResult = {
  variants: ResultBlock[]
  charts: ChartBlock[]
}

// Форма параметров

export type FieldName =
  // Параметры объекта
  | 'objectName'
  | 'objectDiameter'
  | 'objectType'
  | 'objectWidth'
  | 'objectHeight'
  | 'objectLength'
  | 'objectVolume'
  | 'objectMaterial'
  | 'wallThickness'

  // Параметры содержимого
  | 'liquidType'
  | 'liquidDensity' // плотность
  | 'liquidViscosity' // вязкость
  | 'liquidTemperature'
  | 'fillLevel'
  | 'liquidVolume'

  // Параметры вычислительного ядра
  | 'clearanceL'
  | 'crestWidthB'
  | 'plainWallHeight'

export type FormValues = Record<FieldName, number | string | null>

export const EMPTY_FORM: FormValues = {
  objectName: '',
  objectDiameter: 0,
  objectType: 'РВС-5000 · 5 000 м³',
  objectHeight: 0,
  objectLength: 0,
  objectWidth: 0,
  objectVolume: 0,
  objectMaterial: 'Сталь',
  wallThickness: 0,
  liquidType: 'Вода',
  liquidDensity: 0,
  liquidViscosity: 0,
  liquidTemperature: 0,
  fillLevel: 100,
  liquidVolume: 0,

  // Параметры вычислительного ядра
  clearanceL: 3, // Межстенное расстояние
  crestWidthB: 1, // Вылет горизонтального козырька
  plainWallHeight: null, // Высота защитной стенки
}

export const TANK_TYPES = [
  'РВС-700 · 700 м³',
  'РВС-2000 · 2 000 м³',
  'РВС-5000 · 5 000 м³',
  'РВС-10000 · 10 000 м³',
  'РВС-20000 · 20 000 м³',
  'РВС-30000 · 30 000 м³',
] as const

export const TANK_MATERIALS = ['Сталь'] as const

export const LIQUID_TYPES = ['Вода'] as const
