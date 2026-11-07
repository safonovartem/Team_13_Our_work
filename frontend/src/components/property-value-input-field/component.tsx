import styles from './component.module.css';

interface PropertyValueInputFieldProps {
  measurementUnit?: string;
  id?: string;
}

export function PropertyValueInputField({
  measurementUnit,
  id,
}: PropertyValueInputFieldProps) {
  return (
    <div className={styles.container}>
      <input
        type="number"
        id={id}
        className={`${styles.input} ${measurementUnit ? styles.measured : ''}`}
      />
      <span className={styles.propertyMeasureUnit}>{measurementUnit}</span>
    </div>
  );
}
