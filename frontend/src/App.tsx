import { Header } from './components/header/component';
import { Layout } from './components/layout/component';

export function App() {
  return <Layout header={<Header />}></Layout>;
}
