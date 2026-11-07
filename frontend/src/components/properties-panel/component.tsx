import { PropertiesFormGroup } from '../properties-form-group/component';
import { PropertyValueInputField } from '../property-value-input-field/component';
import { SignedFormField } from '../signed-form-field/component';
import styles from './component.module.css';

export function PropertiesPanel() {
  return (
    <div className={styles.container}>
      <section className={styles.propertiesSection}>
        <h3 className={styles.title}>Параметры</h3>
        <form action="#" className={styles.propertiesForm} id="properties-form">
          <PropertiesFormGroup title="Резервуар">
            <SignedFormField title="Уровень заполнения">
              <PropertyValueInputField measurementUnit="м" />
            </SignedFormField>
          </PropertiesFormGroup>
        </form>
      </section>
      <div className={styles.buttons}>
        <button type="reset" className="transparent" form="properties-form">
          Сбросить
        </button>
        <button type="submit" form="properties-form">
          Рассчитать
        </button>
      </div>
    </div>
  );
}
