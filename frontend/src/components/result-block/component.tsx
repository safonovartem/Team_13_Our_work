import { ReactNode } from 'react';
import styles from './component.module.css';

interface ResultBlockProps {
  title: string;
  isImportant?: boolean;
  children: ReactNode;
}

export function ResultBlock({
  title,
  isImportant = false,
  children,
}: ResultBlockProps) {
  return (
    <div
      className={`${styles.resultsBlock} ${isImportant ? styles.important : ''}`}
    >
      <div className={styles.titleContainer}>
        <span className={styles.title}>{title}</span>
      </div>
      <div className={styles.resultInfoContainer}>{children}</div>
    </div>
  );
}
