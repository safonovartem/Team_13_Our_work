import type { WaveResult } from '../../types';
import styles from './component.module.css';

interface ResultWaveStatsProps {
  wave: WaveResult;
}

function fmt(n: number, digits = 2): string {
  if (!Number.isFinite(n)) return '—';
  return n.toFixed(digits);
}

export function ResultWaveStats({ wave }: ResultWaveStatsProps) {
  return (
    <dl className={styles.stats}>
      <div className={styles.row}>
        <dt>Начальная скорость</dt>
        <dd>{fmt(wave.initial_velocity_ms)} м/с</dd>
      </div>
      <div className={styles.row}>
        <dt>Число Фруда</dt>
        <dd>{fmt(wave.froude_number)}</dd>
      </div>
      <div className={styles.row}>
        <dt>Число Струхаля</dt>
        <dd>{fmt(wave.strouhal_number)}</dd>
      </div>
      <div className={styles.row}>
        <dt>Число Рейнольдса</dt>
        <dd>{fmt(wave.reynolds_number, 0)}</dd>
      </div>
      <div className={styles.row}>
        <dt>Масштабный коэффициент</dt>
        <dd>{fmt(wave.scale_factor, 3)}</dd>
      </div>
    </dl>
  );
}
