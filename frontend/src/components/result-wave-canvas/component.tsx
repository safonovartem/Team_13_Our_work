import type { WavePoint } from '../../types';
import styles from './component.module.css';

interface ResultWaveCanvasProps {
  /** текущий кадр */
  point: WavePoint;
  /** максимальные значения для нормализации — считаются по всему trajectory */
  maxDistance: number;
  maxHeight: number;
}

const WIDTH = 480;
const HEIGHT = 200;
const PADDING = 24;

export function ResultWaveCanvas({
  point,
  maxDistance,
  maxHeight,
}: ResultWaveCanvasProps) {
  // нормализация в пиксели
  const x =
    PADDING +
    (maxDistance > 0 ? point.distance_m / maxDistance : 0) *
      (WIDTH - PADDING * 2);
  const h = maxHeight > 0 ? point.wave_height_m / maxHeight : 0;
  const y = HEIGHT - PADDING - h * (HEIGHT - PADDING * 2);

  return (
    <svg
      className={styles.canvas}
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      role="img"
      aria-label="Анимация перелива через защитную стенку"
    >
      {/* земля */}
      <line
        x1={PADDING}
        y1={HEIGHT - PADDING}
        x2={WIDTH - PADDING}
        y2={HEIGHT - PADDING}
        className={styles.ground}
      />

      {/* резервуар (слева) */}
      <rect
        x={PADDING}
        y={HEIGHT - PADDING - 80}
        width={60}
        height={80}
        className={styles.tank}
        rx={4}
      />

      {/* защитная стенка (посередине) */}
      <rect
        x={WIDTH / 2 - 4}
        y={HEIGHT - PADDING - 60}
        width={8}
        height={60}
        className={styles.wall}
      />

      {/* фронт волны — вертикальная «капля» */}
      <circle cx={x} cy={y} r={Math.max(3, h * 18)} className={styles.wave} />

      {/* пунктир траектории до текущего кадра */}
      <line
        x1={PADDING + 60}
        y1={HEIGHT - PADDING - 80}
        x2={x}
        y2={y}
        className={styles.trajectory}
      />
    </svg>
  );
}
