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

export type CalculationResult = {
  variants: ResultBlock[]
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

export type FormValues = Record<FieldName, number | string>

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
}

export const TANK_TYPES = [
  'РВС-2000 · 2 000 м³',
  'РВС-5000 · 5 000 м³',
] as const

export const TANK_MATERIALS = ['Сталь'] as const

export const LIQUID_TYPES = ['Вода'] as const
