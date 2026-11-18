// components/result-wave-canvas/component.tsx
import type { WavePoint } from '../../types';
import styles from './component.module.css';

export interface WaveScene {
  tankDiameterM: number;
  liquidLevelH0M: number;
  clearanceM: number;
  wallHeightM: number;
  crestWidthM: number;
  scenario: 'plain' | 'gwk';
  maxDistanceM: number;
  maxWaveHeightM: number;
}

interface ResultWaveCanvasProps {
  point: WavePoint;
  scene: WaveScene;
}

const WIDTH = 720;
const HEIGHT = 360;
const PADDING = 32;

export function ResultWaveCanvas({ point, scene }: ResultWaveCanvasProps) {
  const {
    tankDiameterM,
    liquidLevelH0M,
    clearanceM,
    wallHeightM,
    crestWidthM,
    scenario,
    maxDistanceM,
    maxWaveHeightM,
  } = scene;

  // ─── единая метрическая система ───
  const worldWidthM =
    tankDiameterM + clearanceM + Math.max(maxDistanceM, clearanceM) + 1;
  const worldHeightM =
    Math.max(liquidLevelH0M, wallHeightM, maxWaveHeightM) + 1;

  const scale = Math.min(
    (WIDTH - 2 * PADDING) / worldWidthM,
    (HEIGHT - 2 * PADDING) / worldHeightM,
  );

  const toPx = (xM: number, yM: number) => ({
    x: PADDING + xM * scale,
    y: HEIGHT - PADDING - yM * scale,
  });

  // ─── резервуар ───
  const tankBL = toPx(0, 0);
  const tankTR = toPx(tankDiameterM, liquidLevelH0M);
  const tankRect = {
    x: tankBL.x,
    y: tankTR.y,
    width: tankTR.x - tankBL.x,
    height: tankBL.y - tankTR.y,
  };

  // ─── стенка ───
  const wallXM = tankDiameterM + clearanceM;
  const wallBL = toPx(wallXM, 0);
  const wallTR = toPx(wallXM, wallHeightM);
  const wallRect = {
    x: wallBL.x - 4,
    y: wallTR.y,
    width: 8,
    height: wallBL.y - wallTR.y,
  };

  // ─── козырёк (только gwk) ───
  const crestRect =
    scenario === 'gwk' && crestWidthM > 0
      ? (() => {
          const right = toPx(wallXM, wallHeightM);
          const left = toPx(wallXM - crestWidthM, wallHeightM);
          return {
            x: left.x,
            y: right.y - 3,
            width: Math.max(1, right.x - left.x),
            height: 6,
          };
        })()
      : null;

  // ─── волна ───
  const waveXM = tankDiameterM + point.distance_m;
  const waveYM = point.wave_height_m;
  const reachedWall = waveXM >= wallXM;
  const overflows = reachedWall && waveYM > wallHeightM;
  const displayWaveXM = reachedWall && !overflows ? wallXM : waveXM;
  const wavePx = toPx(displayWaveXM, waveYM);

  const startPx = toPx(tankDiameterM, liquidLevelH0M);
  const radius = Math.max(3, Math.min(12, waveYM * scale * 0.15));

  return (
    <svg
      className={styles.canvas}
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      role="img"
      aria-label="Схема перелива через защитную стенку"
    >
      {/* земля */}
      <line
        x1={PADDING}
        y1={HEIGHT - PADDING}
        x2={WIDTH - PADDING}
        y2={HEIGHT - PADDING}
        className={styles.ground}
      />

      {/* резервуар */}
      <rect {...tankRect} className={styles.tank} rx={4} />
      <text
        x={tankRect.x + tankRect.width / 2}
        y={tankRect.y - 6}
        textAnchor="middle"
        className={styles.label}
      >
        РВС
      </text>

      {/* стенка */}
      <rect {...wallRect} className={styles.wall} />
      <text
        x={wallRect.x + wallRect.width / 2}
        y={wallRect.y - 6}
        textAnchor="middle"
        className={styles.label}
      >
        {wallHeightM.toFixed(2)} м
      </text>

      {/* козырёк */}
      {crestRect && <rect {...crestRect} className={styles.crest} />}

      {/* пунктир (только пока волна не дошла до стенки) */}
      {!reachedWall && (
        <line
          x1={startPx.x}
          y1={startPx.y}
          x2={wavePx.x}
          y2={wavePx.y}
          className={styles.trajectory}
        />
      )}

      {/* волна */}
      <circle
        cx={wavePx.x}
        cy={wavePx.y}
        r={radius}
        className={`${styles.wave} ${overflows ? styles.waveOverflow : ''}`}
      />

      {/* подпись */}
      <text x={PADDING} y={HEIGHT - 6} className={styles.caption}>
        l = {clearanceM} м · h₀ = {liquidLevelH0M} м ·{' '}
        {scenario === 'gwk' ? 'ГВК' : 'без козырька'}
      </text>
    </svg>
  );
}

export type { ResultWaveCanvasProps };
