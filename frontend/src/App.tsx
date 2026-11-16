import { useState } from 'react';
import { Header } from './components/header/component';
import { Layout } from './components/layout/component';
import { PropertiesPanel } from './components/properties-panel/component';
import { ResultBlock } from './components/result-block/component';
import { ResultSection } from './components/result-section/component';
import { ResultString } from './components/result-string/component';
import { FormValues, EMPTY_FORM, CalculationResult } from './types';
import { ResultPlaceholder } from './components/result-placeholder/component';
import { calculate } from './mock-api';
import { ResultLineChart } from './components/result-line-chart/component';

export function App() {
  const [form, setForm] = useState<FormValues>(EMPTY_FORM);
  const [result, setResult] = useState<CalculationResult | null>(null);

  const handleSubmit = async (values: FormValues) => {
    try {
      const data = await calculate(values);
      setResult(data);
    } finally {
    }
  };

  return (
    <Layout
      header={<Header />}
      aside={
        <PropertiesPanel
          values={form}
          onChange={setForm}
          onSubmit={handleSubmit}
          onReset={() => setForm(EMPTY_FORM)}
        />
      }
    >
      {!result && <ResultPlaceholder title="Результаты расчёта" />}
      {result && (
        <ResultSection title="Сравнение вариантов">
          {result.variants.map((block) => {
            return (
              <ResultBlock
                key={block.id}
                title={block.title}
                isImportant={block.isImportant}
              >
                {block.items.map((resultString, index) => {
                  return (
                    <ResultString
                      key={index}
                      title={resultString.title}
                      value={resultString.value}
                    />
                  );
                })}
              </ResultBlock>
            );
          })}
          {result.charts.map(({ title, datasets }) => {
            return (
              <ResultBlock title={title}>
                <ResultLineChart datasets={datasets} />
              </ResultBlock>
            );
          })}
        </ResultSection>
      )}
    </Layout>
  );
}
