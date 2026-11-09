import { Header } from './components/header/component';
import { Layout } from './components/layout/component';
import { PropertiesPanel } from './components/properties-panel/component';
import { ResultBlock } from './components/result-block/component';
import { ResultSection } from './components/result-section/component';

export function App() {
  return (
    <Layout header={<Header />} aside={<PropertiesPanel />}>
      <ResultSection title="Результаты расчёта">
        <ResultBlock title="Без козырька">
          <div className="resultValue">Доля перелива</div>
          <div className="resultValue">Стоимость</div>
        </ResultBlock>
      </ResultSection>
    </Layout>
  );
}
