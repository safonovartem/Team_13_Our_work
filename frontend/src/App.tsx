import { Header } from './components/header/component';
import { Layout } from './components/layout/component';
import { PropertiesPanel } from './components/properties-panel/component';
import { ResultBlock } from './components/result-block/component';
import { ResultSection } from './components/result-section/component';
import { ResultString } from './components/result-string/component';

export function App() {
  return (
    <Layout header={<Header />} aside={<PropertiesPanel />}>
      <ResultSection title="Сравнение вариантов">
        <ResultBlock title="Без козырька">
          <ResultString title="Доля перелива" value="31%" />
          <ResultString title="Стоимость" value="12 млн ₽" />
          <ResultString title="Безопасность" value="Низкая" />
          <ResultString title="Реализуемость" value="Высокая" />
        </ResultBlock>
        <ResultBlock title="С ГВК" isImportant={true}>
          <ResultString title="Доля перелива" value="12 %" />
          <ResultString title="Стоимость" value="16 млн ₽" />
          <ResultString title="Безопасность" value="Высокая" />
          <ResultString title="Реализуемость" value="Хорошая" />
        </ResultBlock>
        <ResultBlock title="С НВК">
          <ResultString title="Доля перелива" value="9 %" />
          <ResultString title="Стоимость" value="21 млн ₽" />
          <ResultString title="Безопасность" value="Высокая" />
          <ResultString title="Реализуемость" value="Средняя" />
        </ResultBlock>
      </ResultSection>
    </Layout>
  );
}
