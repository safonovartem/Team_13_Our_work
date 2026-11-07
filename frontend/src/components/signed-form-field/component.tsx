import { cloneElement, ReactElement, useId } from 'react';
import styles from './component.module.css';
import { MeaningNote } from '../meaning-note/component';

interface SignedFormFieldProps {
  title: string;
  valueNoteMessage?: string;
  id?: string;
  children: ReactElement<{ id?: string }>;
}

export function SignedFormField({
  title,
  valueNoteMessage,
  id,
  children,
}: SignedFormFieldProps) {
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
      {valueNoteMessage && <MeaningNote>{valueNoteMessage}</MeaningNote>}
    </div>
  );
}
