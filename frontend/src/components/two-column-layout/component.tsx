import { ReactNode } from 'react';
import styles from './component.module.css';

interface TwoColumnLayoutProps {
  children: ReactNode;
}

export function TwoColumnLayout({ children }: TwoColumnLayoutProps) {
  return <div className={styles.container}>{children}</div>;
}
