import { ReactNode, useId } from 'react';
import styles from './component.module.css';

interface PropertiesFormGroupProps {
  title: string;
  children: ReactNode;
}

export function PropertiesFormGroup({
  title,
  children,
}: PropertiesFormGroupProps) {
  const titleId = useId();
  return (
    <div className={styles.container} role="group" aria-labelledby={titleId}>
      <span className={styles.title} id={titleId}>
        {title}
      </span>
      <div className={styles.inputFields}>{children}</div>
    </div>
  );
}
