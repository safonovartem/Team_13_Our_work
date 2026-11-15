import { useState } from 'react';
import { Header } from './components/header/component';
import { Layout } from './components/layout/component';
import { PropertiesPanel } from './components/properties-panel/component';
import { ResultBlock } from './components/result-block/component';
import { ResultSection } from './components/result-section/component';
import { ResultString } from './components/result-string/component';
import { FormValues, EMPTY_FORM, CalculationResult } from './types';
import { ResultPlaceholder } from './components/result-placeholder/component';

export function App() {
  const [form, setForm] = useState<FormValues>(EMPTY_FORM);
  const [result, setResult] = useState<CalculationResult | null>(null);

  return (
    <Layout
      header={<Header />}
      aside={<PropertiesPanel values={form} onChange={setForm} />}
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
        </ResultSection>
      )}
    </Layout>
  );
}
