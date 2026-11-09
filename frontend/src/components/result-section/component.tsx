import { ReactNode } from 'react';
import styles from './component.module.css';

interface ResultSectionProps {
  title: string;
  children: ReactNode;
}

export function ResultSection({ title, children }: ResultSectionProps) {
  return (
    <section className={styles.resultSection}>
      <h3>{title}</h3>
      <div className={styles.resultsLayout}>{children}</div>
    </section>
  );
}
