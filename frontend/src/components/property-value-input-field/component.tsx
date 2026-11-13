import styles from './component.module.css';

interface PropertyValueInputFieldProps {
  type: 'number' | 'text';
  placeholder?: string;
  measurementUnit?: string;
  id?: string;
}

export function PropertyValueInputField({
  type,
  placeholder = 'Введите значение...',
  measurementUnit,
  id,
}: PropertyValueInputFieldProps) {
  return (
    <div className={styles.container}>
      <input
        placeholder={placeholder}
        type={type}
        id={id}
        className={`${styles.input} ${measurementUnit ? styles.measured : ''}`}
      />
      <span className={styles.propertyMeasureUnit}>{measurementUnit}</span>
    </div>
  );
}
