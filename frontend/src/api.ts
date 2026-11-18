// src/api.ts
import type {
  CalculationResult,
  FormValues,
  ResultBlock,
  ChartBlock,
  WaveResult,
} from './types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

// ─── toRequest: FormValues → тело from-form ─────────

interface FromFormRequest {
  objectType: string
  objectVolume?: number
  clearanceL?: number
  crestWidthB?: number
  plainWallHeight?: number
  scenarios?: ('plain' | 'gwk')[]
}

export function toRequest(form: FormValues): FromFormRequest {
  return {
    objectType: String(form.objectType),
    objectVolume: toOptionalNumber(form.objectVolume),
    clearanceL: toOptionalNumber(form.clearanceL),
    crestWidthB: toOptionalNumber(form.crestWidthB),
    plainWallHeight: toOptionalNumber(form.plainWallHeight),
    scenarios: ['plain', 'gwk'],
  }
}

function toOptionalNumber(
  v: number | string | undefined | null,
): number | undefined {
  if (v === '' || v === undefined || v === null) return undefined
  const n = Number(v)
  return Number.isFinite(n) ? n : undefined
}

// ─── toCalculationResult: сырой ответ → ваш тип ─────

export function toCalculationResult(raw: any): CalculationResult {
  return {
    variants: (raw.variants ?? []).map(
      (v: any): ResultBlock => ({
        id: v.id,
        title: v.title,
        isImportant: Boolean(v.isImportant),
        items: (v.items ?? []).map((i: any) => ({
          title: i.title,
          value: i.value,
        })),
      }),
    ),
    charts: (raw.charts ?? []).map(
      (c: any): ChartBlock => ({
        title: c.title,
        datasets: (c.datasets ?? []).map((d: any) => ({
          label: d.label,
          data: d.data as [number, number][],
        })),
        xAxis: c.xAxis
          ? { title: c.xAxis.title, unit: c.xAxis.unit }
          : undefined,
        yAxis: c.yAxis
          ? { title: c.yAxis.title, unit: c.yAxis.unit }
          : undefined,
      }),
    ),
    wave: raw.result?.wave as WaveResult | undefined,
    recommendedVariant:
      raw.recommended_variant ?? raw.result?.recommended_variant,
  }
}

export class ApiError extends Error {
  readonly status: number
  readonly code?: string
  readonly field?: string

  constructor(status: number, message: string, code?: string, field?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.field = field
  }
}

export async function calculate(form: FormValues): Promise<CalculationResult> {
  const response = await fetch(`${BASE_URL}/api/calculations/from-form`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(toRequest(form)),
  })

  if (!response.ok) {
    const body = await response.json().catch(() => null)

    // 422 от Pydantic: detail — массив объектов с loc/msg
    if (Array.isArray(body?.detail)) {
      const first = body.detail[0]
      const field = Array.isArray(first?.loc)
        ? first.loc[first.loc.length - 1]
        : undefined
      throw new ApiError(
        response.status,
        first?.msg ?? 'Ошибка валидации',
        body.code,
        field,
      )
    }

    // доменная ошибка: { detail: string, code }
    const message =
      typeof body?.detail === 'string'
        ? body.detail
        : `Ошибка расчёта (${response.status})`

    throw new ApiError(response.status, message, body?.code, body?.field)
  }

  return toCalculationResult(await response.json())
}
