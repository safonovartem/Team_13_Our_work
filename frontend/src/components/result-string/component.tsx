import styles from './component.module.css';

interface ResultStringProps {
  title: string;
  value: string;
}

export function ResultString({ title, value }: ResultStringProps) {
  return (
    <div className={styles.container}>
      <span className={styles.resultTitle}>{title}</span>
      <span className={styles.resultValue}>{value}</span>
    </div>
  );
}
