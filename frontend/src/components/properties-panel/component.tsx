import styles from './component.module.css';

export function PropertiesPanel() {
  return (
    <div className={styles.container}>
      <section className={styles.propertiesSection}>
        <h3 className={styles.title}>Параметры</h3>
        <form
          action="#"
          className={styles.propertiesForm}
          id="properties-form"
        ></form>
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
