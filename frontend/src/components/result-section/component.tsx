import { ReactNode } from 'react';
import styles from './component.module.css';

interface ResultSectionProps {
  title: string;
  children: ReactNode;
  /** 'grid' — 3 колонки (по умолчанию), 'single' — одна колонка на всю ширину */
  layout?: 'grid' | 'single';
}

export function ResultSection({
  title,
  children,
  layout = 'grid',
}: ResultSectionProps) {
  return (
    <section className={styles.resultSection}>
      <h3>{title}</h3>
      <div
        className={`${styles.resultsLayout} ${
          layout === 'single' ? styles.single : ''
        }`}
      >
        {children}
      </div>
    </section>
  );
}
