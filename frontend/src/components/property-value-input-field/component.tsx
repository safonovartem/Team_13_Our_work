import styles from './component.module.css';

interface PropertyValueInputFieldProps {
  type: 'number' | 'text';
  measurementUnit?: string;
  id?: string;
}

export function PropertyValueInputField({
  type,
  measurementUnit,
  id,
}: PropertyValueInputFieldProps) {
  return (
    <div className={styles.container}>
      <input
        type={type}
        id={id}
        className={`${styles.input} ${measurementUnit ? styles.measured : ''}`}
      />
      <span className={styles.propertyMeasureUnit}>{measurementUnit}</span>
    </div>
  );
}
