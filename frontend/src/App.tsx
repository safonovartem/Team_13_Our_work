import { Header } from './components/header/component';
import { Layout } from './components/layout/component';
import { PropertiesPanel } from './components/properties-panel/component';

export function App() {
  return <Layout header={<Header />} aside={<PropertiesPanel />}></Layout>;
}
