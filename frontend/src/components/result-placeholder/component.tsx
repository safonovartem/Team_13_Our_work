import styles from './component.module.css';

interface ResultPlaceholderProps {
  title: string;
}

export function ResultPlaceholder({ title }: ResultPlaceholderProps) {
  return (
    <section className={styles.placeholderSection}>
      <h3>{title}</h3>
      <div className={styles.container}>
        <span className={styles.placeholderTitle}>Результатов пока нет</span>
        <p className={styles.placeholderMessage}>
          Задайте параметры слева и нажмите «Рассчитать». Здесь появятся расчёт
          перелива, сравнение вариантов защиты и рекомендации.
        </p>
      </div>
    </section>
  );
}
