import {
  FieldName,
  FormValues,
  LIQUID_TYPES,
  TANK_MATERIALS,
  TANK_TYPES,
} from '../../types';
import { DropdownMenu } from '../dropdown-menu/component';
import { PropertiesFormGroup } from '../properties-form-group/component';
import { PropertyValueInputField } from '../property-value-input-field/component';
import { SignedFormField } from '../signed-form-field/component';
import styles from './component.module.css';

interface PropertiesPanelProps {
  values: FormValues;
  onChange: (next: FormValues) => void;
  onSubmit: (values: FormValues) => void;
  onReset: () => void;
  loading?: boolean;
}

export function PropertiesPanel({
  values,
  onChange,
  onReset,
  onSubmit,
  loading = false,
}: PropertiesPanelProps) {
  const setField = (name: FieldName) => (raw: string | number | null) =>
    onChange({ ...values, [name]: raw });

  const handleSubmit = (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    onSubmit(values);
  };

  return (
    <div className={styles.container}>
      <section className={styles.propertiesSection}>
        <h3 className={styles.title}>Параметры</h3>
        <form
          onSubmit={handleSubmit}
          onReset={onReset}
          className={styles.propertiesForm}
          id="properties-form"
        >
          <PropertiesFormGroup title="Резервуар">
            <SignedFormField title="Тип и объём">
              <DropdownMenu
                data={TANK_TYPES}
                value={values.objectType!}
                onChange={setField('objectType')}
              />
            </SignedFormField>
            <SignedFormField title="Межстенное расстояние">
              <PropertyValueInputField
                type="number"
                measurementUnit="м"
                value={values.clearanceL}
                onChange={setField('clearanceL')}
              />
            </SignedFormField>
            <SignedFormField title="Вылет горизонтального козырька">
              <PropertyValueInputField
                type="number"
                measurementUnit="м"
                value={values.crestWidthB}
                onChange={setField('crestWidthB')}
              />
            </SignedFormField>
            <SignedFormField
              title="Высота защитной стенки"
              valueNoteMessage="Необязательное значение"
            >
              <PropertyValueInputField
                type="number"
                measurementUnit="м"
                value={values.plainWallHeight}
                onChange={setField('plainWallHeight')}
              />
            </SignedFormField>
          </PropertiesFormGroup>
        </form>
      </section>
      <div className={styles.buttons}>
        <button
          type="reset"
          className="transparent"
          form="properties-form"
          disabled={loading}
        >
          Сбросить
        </button>
        <button type="submit" form="properties-form" disabled={loading}>
          Рассчитать
        </button>
      </div>
    </div>
  );
}
