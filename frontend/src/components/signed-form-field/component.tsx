import { cloneElement, ReactElement, useId } from 'react';
import styles from './component.module.css';

interface SignedFormFieldProps {
  title: string;
  id?: string;
  children: ReactElement<{ id?: string }>;
}

export function SignedFormField({ title, id, children }: SignedFormFieldProps) {
  const autoId = useId();
  const childId = children.props.id;
  const fieldId = id ?? childId ?? autoId;

  const child = cloneElement(children, { id: fieldId });

  return (
    <div className={styles.container}>
      <label htmlFor={fieldId} className={styles.title}>
        {title}
      </label>
      {child}
    </div>
  );
}
