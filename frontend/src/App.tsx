// App.tsx
import { useState } from 'react';
import { Header } from './components/header/component';
import { Layout } from './components/layout/component';
import { PropertiesPanel } from './components/properties-panel/component';
import { ResultBlock } from './components/result-block/component';
import { ResultSection } from './components/result-section/component';
import { ResultString } from './components/result-string/component';
import { ResultPlaceholder } from './components/result-placeholder/component';
import { ResultLineChart } from './components/result-line-chart/component';
import { ResultWaveAnimation } from './components/result-wave-animation/component';
import { ToastStack } from './components/toast-stack/component';
import { calculate, ApiError } from './api';
import { useToasts } from './hooks/use-toasts';
import { FormValues, EMPTY_FORM, CalculationResult } from './types';

export function App() {
  const [form, setForm] = useState<FormValues>(EMPTY_FORM);
  const [result, setResult] = useState<CalculationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const { toasts, push, dismiss } = useToasts();

  const handleSubmit = async (values: FormValues) => {
    setLoading(true);
    try {
      const data = await calculate(values);
      setResult(data);
    } catch (e) {
      const message =
        e instanceof ApiError
          ? e.message
          : e instanceof Error
            ? e.message
            : 'Неизвестная ошибка';
      push(message, 'error');
      // результат остаётся предыдущий
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setForm(EMPTY_FORM);
    setResult(null);
  };

  return (
    <>
      <Layout
        header={<Header />}
        aside={
          <PropertiesPanel
            values={form}
            onChange={setForm}
            onSubmit={handleSubmit}
            onReset={handleReset}
            loading={loading}
          />
        }
      >
        {loading && (
          <ResultPlaceholder
            title="Результаты расчёта"
            variant="loading"
            message="Идёт расчёт…"
          />
        )}

        {!loading && !result && (
          <ResultPlaceholder title="Результаты расчёта" />
        )}

        {!loading && result && (
          <>
            <ResultSection title="Сравнение вариантов">
              {result.variants.map((block) => (
                <ResultBlock
                  key={block.id}
                  title={block.title}
                  isImportant={block.isImportant}
                >
                  {block.items.map((item) => (
                    <ResultString
                      key={item.title}
                      title={item.title}
                      value={item.value}
                    />
                  ))}
                </ResultBlock>
              ))}
            </ResultSection>

            {result.wave && (
              <ResultSection
                title="Перелив через защитную стенку"
                layout="single"
              >
                <ResultBlock title="Анимация фронта волны">
                  <ResultWaveAnimation wave={result.wave} />
                </ResultBlock>
              </ResultSection>
            )}

            {result.charts.length > 0 && (
              <ResultSection title="Графики">
                {result.charts.map(({ title, datasets, xAxis, yAxis }) => (
                  <ResultBlock key={title} title={title}>
                    <ResultLineChart
                      datasets={datasets}
                      xAxis={xAxis}
                      yAxis={yAxis}
                    />
                  </ResultBlock>
                ))}
              </ResultSection>
            )}
          </>
        )}
      </Layout>

      <ToastStack toasts={toasts} onDismiss={dismiss} />
    </>
  );
}
