import { DropdownMenu } from '../dropdown-menu/component';
import { MeaningNote } from '../meaning-note/component';
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
            <SignedFormField title="Тип и объём">
              <DropdownMenu
                data={['РВС-2000 · 2 000 м³', 'РВС-5000 · 5 000 м³']}
              />
            </SignedFormField>
            <SignedFormField title="Уровень заполнения">
              <PropertyValueInputField measurementUnit="%" />
            </SignedFormField>
          </PropertiesFormGroup>

          <PropertiesFormGroup title="Защитная стенка">
            <div className={styles.twoColumn}>
              <SignedFormField title="Высота стенки">
                <PropertyValueInputField measurementUnit="м" />
              </SignedFormField>
              <SignedFormField title="Высота стенки">
                <PropertyValueInputField measurementUnit="м" />
              </SignedFormField>
            </div>
            <MeaningNote>
              Подтверждённый диапазон межстенного расстояния: 1,5–3 м
            </MeaningNote>
          </PropertiesFormGroup>

          <PropertiesFormGroup title="Волноотражающий козырёк">
            <SignedFormField
              title="Вылет козырька"
              valueNoteMessage="Подтверждённый диапазон: 0,5–1,5 м"
            >
              <PropertyValueInputField measurementUnit="м" />
            </SignedFormField>
          </PropertiesFormGroup>

          <PropertiesFormGroup title="Дополнительное ограждение">
            <SignedFormField title="Высота ограждения">
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
