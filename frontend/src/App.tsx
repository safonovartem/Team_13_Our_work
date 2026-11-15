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
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
);

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
          <ResultBlock title="Доля перелива от высоты стенки">
            <Line
              data={{
                datasets: [
                  {
                    data: [
                      [0.7, 10],
                      [0.97, 0],
                      [1.1, 0],
                    ],
                    label: 'I = 3.0 м',
                  },
                ],
              }}
              options={{
                scales: {
                  x: {
                    beginAtZero: false,
                    type: 'linear',
                  },
                },
              }}
            />
          </ResultBlock>
        </ResultSection>
      )}
    </Layout>
  );
}
