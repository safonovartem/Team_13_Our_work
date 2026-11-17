// src/api.ts
import type {
  CalculationResult,
  FormValues,
  ResultBlock,
  ChartBlock,
} from './types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

// ─── toRequest: FormValues → тело from-form ─────────

interface FromFormRequest {
  objectType: string
  objectVolume?: number
  clearanceL?: number
  crestWidthB?: number
  plainWallHeight?: number
  scenarios?: 'plain'[]
}

export function toRequest(form: FormValues): FromFormRequest {
  return {
    objectType: String(form.objectType),
    objectVolume: toOptionalNumber(form.objectVolume),
    clearanceL: toOptionalNumber(form.clearanceL),
    crestWidthB: toOptionalNumber(form.crestWidthB),
    plainWallHeight: toOptionalNumber(form.plainWallHeight),
    scenarios: ['plain'],
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
      }),
    ),
  }
}

// ─── calculate: публичная точка входа ───────────────

export async function calculate(form: FormValues): Promise<CalculationResult> {
  const response = await fetch(`${BASE_URL}/api/calculations/from-form`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(toRequest(form)),
  })

  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const message =
      typeof body?.detail === 'string'
        ? body.detail
        : `Ошибка расчёта (${response.status})`
    throw new Error(message)
  }

  return toCalculationResult(await response.json())
}
