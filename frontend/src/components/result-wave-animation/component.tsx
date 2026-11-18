// components/result-wave-animation/component.tsx
import { useEffect, useMemo, useState } from 'react';
import type { WaveResult } from '../../types';
import {
  ResultWaveCanvas,
  type WaveScene,
} from '../result-wave-canvas/component';
import { ResultWaveStats } from '../result-wave-stats/component';
import styles from './component.module.css';

interface ResultWaveAnimationProps {
  wave: WaveResult;
  scene: WaveScene;
  frameDuration?: number;
}

export function ResultWaveAnimation({
  wave,
  scene,
  frameDuration = 200,
}: ResultWaveAnimationProps) {
  const trajectory = wave.trajectory ?? [];
  const total = trajectory.length;

  const [frame, setFrame] = useState(0);
  const [playing, setPlaying] = useState(false);

  // maxDistance/maxHeight теперь считаются в App и приходят в scene,
  // но на случай, если scene неполный — подстрахуемся
  const safeScene = useMemo<WaveScene>(() => {
    let md = scene.maxDistanceM;
    let mh = scene.maxWaveHeightM;
    for (const p of trajectory) {
      if (p.distance_m > md) md = p.distance_m;
      if (p.wave_height_m > mh) mh = p.wave_height_m;
    }
    return { ...scene, maxDistanceM: md, maxWaveHeightM: mh };
  }, [scene, trajectory]);

  useEffect(() => {
    if (!playing || total <= 1) return;
    const id = setInterval(() => {
      setFrame((f) => {
        if (f + 1 >= total) {
          setPlaying(false);
          return total - 1;
        }
        return f + 1;
      });
    }, frameDuration);
    return () => clearInterval(id);
  }, [playing, total, frameDuration]);

  if (total === 0) {
    return <p className={styles.empty}>Данных для анимации нет</p>;
  }

  const current = trajectory[Math.min(frame, total - 1)];

  return (
    <div className={styles.wrapper}>
      <ResultWaveCanvas point={current} scene={safeScene} />

      <div className={styles.controls}>
        <button
          type="button"
          onClick={() => setPlaying((p) => !p)}
          disabled={total <= 1}
        >
          {playing ? 'Пауза' : 'Играть'}
        </button>
        <button
          type="button"
          onClick={() => {
            setPlaying(false);
            setFrame(0);
          }}
        >
          Сброс
        </button>
        <input
          type="range"
          min={0}
          max={Math.max(0, total - 1)}
          value={frame}
          onChange={(e) => {
            setPlaying(false);
            setFrame(Number(e.target.value));
          }}
          aria-label="Кадр анимации"
        />
        <span className={styles.counter}>
          {frame + 1} / {total}
        </span>
      </div>

      <div className={styles.meta}>
        <span>t = {current.time_s.toFixed(3)} с</span>
        <span>расстояние = {current.distance_m.toFixed(2)} м</span>
        <span>высота = {current.wave_height_m.toFixed(2)} м</span>
      </div>

      <ResultWaveStats wave={wave} />
    </div>
  );
}
