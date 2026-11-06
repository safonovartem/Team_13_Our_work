import styles from './component.module.css';
import logo from '../../assets/logo.svg';

export function Header() {
  return (
    <div className={styles.container}>
      <div className={styles.info}>
        <a href="/" className={styles.logo}>
          <img src={logo} alt="logo" className={styles.logoImg} />
          Tank Safety Platform
        </a>
        <div className={styles.verticalLine}></div>
        <span className={styles.title}>РВС-2000 Аварийный сценарий</span>
      </div>
      <div className={styles.buttons}>
        <button type="button" className="transparent">
          Сохранить
        </button>
        <button type="button">Отчёт</button>
      </div>
    </div>
  );
}
