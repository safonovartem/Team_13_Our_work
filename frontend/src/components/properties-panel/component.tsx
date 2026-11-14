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
}

export function PropertiesPanel({ values, onChange }: PropertiesPanelProps) {
  const setField = (name: FieldName) => (raw: string | number) =>
    onChange({ ...values, [name]: raw });

  return (
    <div className={styles.container}>
      <section className={styles.propertiesSection}>
        <h3 className={styles.title}>Параметры</h3>
        <form action="#" className={styles.propertiesForm} id="properties-form">
          <PropertiesFormGroup title="Резервуар">
            <SignedFormField title="Название объекта">
              <PropertyValueInputField
                value={values.objectName}
                onChange={setField('objectName')}
              />
            </SignedFormField>
            <SignedFormField title="Тип и объём">
              <DropdownMenu
                data={TANK_TYPES}
                value={values.objectType}
                onChange={setField('objectType')}
              />
            </SignedFormField>
            <SignedFormField title="Диаметр">
              <PropertyValueInputField
                type="number"
                measurementUnit="м"
                value={values.objectDiameter}
                onChange={setField('objectDiameter')}
              />
            </SignedFormField>
            <div className={styles.twoColumn}>
              <SignedFormField title="Ширина">
                <PropertyValueInputField
                  type="number"
                  measurementUnit="м"
                  value={values.objectWidth}
                  onChange={setField('objectWidth')}
                />
              </SignedFormField>
              <SignedFormField title="Высота">
                <PropertyValueInputField
                  type="number"
                  measurementUnit="м"
                  value={values.objectHeight}
                  onChange={setField('objectHeight')}
                />
              </SignedFormField>
              <SignedFormField title="Длина">
                <PropertyValueInputField
                  type="number"
                  measurementUnit="м"
                  value={values.objectLength}
                  onChange={setField('objectLength')}
                />
              </SignedFormField>
              <SignedFormField title="Объём">
                <PropertyValueInputField
                  type="number"
                  measurementUnit="м³"
                  value={values.objectVolume}
                  onChange={setField('objectVolume')}
                />
              </SignedFormField>
            </div>
            <SignedFormField title="Материал">
              <DropdownMenu
                data={TANK_MATERIALS}
                value={values.objectMaterial}
                onChange={setField('objectMaterial')}
              />
            </SignedFormField>
            <SignedFormField title="Толщина стены">
              <PropertyValueInputField
                type="number"
                measurementUnit="м"
                value={values.wallThickness}
                onChange={setField('wallThickness')}
              />
            </SignedFormField>
          </PropertiesFormGroup>

          <PropertiesFormGroup title="Параметры содержимого">
            <SignedFormField title="Тип жидкости">
              <DropdownMenu
                data={LIQUID_TYPES}
                value={values.liquidType}
                onChange={setField('liquidType')}
              />
            </SignedFormField>
            <SignedFormField title="Плотность">
              <PropertyValueInputField
                type="number"
                measurementUnit="кг/м³"
                value={values.liquidDensity}
                onChange={setField('liquidDensity')}
              />
            </SignedFormField>
            <SignedFormField title="Вязкость">
              <PropertyValueInputField
                type="number"
                value={values.liquidViscosity}
                onChange={setField('liquidViscosity')}
              />
            </SignedFormField>
            <SignedFormField title="Температура">
              <PropertyValueInputField
                type="number"
                measurementUnit="K"
                value={values.liquidTemperature}
                onChange={setField('liquidTemperature')}
              />
            </SignedFormField>
            <SignedFormField title="Уровень заполнения">
              <PropertyValueInputField
                type="number"
                measurementUnit="%"
                value={values.fillLevel}
                onChange={setField('fillLevel')}
              />
            </SignedFormField>
            <SignedFormField title="Объём жидкости">
              <PropertyValueInputField
                type="number"
                measurementUnit="м³"
                value={values.liquidVolume}
                onChange={setField('liquidVolume')}
              />
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
