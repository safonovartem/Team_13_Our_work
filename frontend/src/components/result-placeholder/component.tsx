import styles from './component.module.css';

interface ResultPlaceholderProps {
  title: string;
  message?: string;
  variant?: 'empty' | 'loading';
}

const DEFAULT_MESSAGES = {
  empty:
    'Задайте параметры слева и нажмите «Рассчитать». Здесь появятся расчёт перелива, сравнение вариантов защиты и рекомендации.',
  loading: 'Идёт расчёт…',
} as const;

export function ResultPlaceholder({
  title,
  message,
  variant = 'empty',
}: ResultPlaceholderProps) {
  return (
    <section className={styles.placeholderSection}>
      <h3>{title}</h3>
      <div
        className={styles.container}
        aria-busy={variant === 'loading' || undefined}
      >
        {variant === 'loading' && <span className={styles.spinner} />}
        <span className={styles.placeholderTitle}>
          {variant === 'loading' ? 'Расчёт' : 'Результатов пока нет'}
        </span>
        <p className={styles.placeholderMessage}>
          {message ?? DEFAULT_MESSAGES[variant]}
        </p>
      </div>
    </section>
  );
}
