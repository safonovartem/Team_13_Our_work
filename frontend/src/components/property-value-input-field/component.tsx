import styles from './component.module.css';

interface PropertyValueInputFieldProps {
  type?: 'number' | 'text';
  value: string | number;
  onChange: (raw: string | number) => void;
  placeholder?: string;
  measurementUnit?: string;
  id?: string;
  name?: string;
  disabled?: boolean;
}

export function PropertyValueInputField({
  type = 'text',
  placeholder = 'Введите значение...',
  value,
  onChange,
  measurementUnit,
  id,
  name,
  disabled,
}: PropertyValueInputFieldProps) {
  return (
    <div className={styles.container}>
      <input
        type={type}
        id={id}
        name={name}
        disabled={disabled}
        placeholder={placeholder}
        value={value}
        onChange={(e) =>
          onChange(type === 'number' ? Number(e.target.value) : e.target.value)
        }
        className={`${styles.input} ${measurementUnit ? styles.measured : ''}`}
      />
      {measurementUnit && (
        <span className={styles.propertyMeasureUnit}>{measurementUnit}</span>
      )}
    </div>
  );
}
