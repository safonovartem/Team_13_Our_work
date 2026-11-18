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

// название осей графиков
export type ChartAxis = {
  title?: string
  unit?: string
}

export type ChartBlock = {
  title: string
  datasets: ChartDataset<'line', ([number, number] | Point | null)[]>[]
  xAxis?: ChartAxis
  yAxis?: ChartAxis
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

// Перелив воды

export type WavePoint = {
  time_s: number
  distance_m: number
  wave_height_m: number
}

export type WaveResult = {
  initial_velocity_ms: number
  froude_number: number
  strouhal_number: number
  reynolds_number: number
  scale_factor: number
  trajectory: WavePoint[]
}

// расширяем CalculationResult — но сервер кладёт wave внутрь result,
// поэтому добавим отдельный тип для «сырого» ответа
export type RawCalculationResponse = {
  variants: ResultBlock[]
  charts: ChartBlock[]
  result?: {
    wave?: WaveResult
    recommended_variant?: string
  }
  recommended_variant?: string
}

export type VariantMeta = {
  scenario: 'plain' | 'gwk'
  wallHeightM: number
  crestWidthM: number
  overflowPct: number
  safetyScore: number
}

export type CalculationResult = {
  variants: ResultBlock[]
  charts: ChartBlock[]
  wave?: WaveResult
  recommendedVariant?: string

  // для сцены
  tankDiameterM?: number
  liquidLevelH0M?: number
  clearanceL?: number
  variantMeta?: VariantMeta[]
}
