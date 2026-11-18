// components/result-line-chart/component.tsx
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartDataset,
  Point,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import type { ChartAxis } from '../../types';
import { colorForIndex } from './palette';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
);

interface ResultLineChartProps {
  datasets: ChartDataset<'line', ([number, number] | Point | null)[]>[];
  xAxis?: ChartAxis;
  yAxis?: ChartAxis;
}

function formatAxisLabel(axis?: ChartAxis): string | undefined {
  if (!axis) return undefined;
  const title = axis.title?.trim();
  const unit = axis.unit?.trim();
  if (title && unit) return `${title}, ${unit}`;
  return title || unit || undefined;
}

/** Раскрашивает datasets палитрой по индексу, не мутируя входной массив */
function withColors(
  datasets: ChartDataset<'line', ([number, number] | Point | null)[]>[],
): ChartDataset<'line', ([number, number] | Point | null)[]>[] {
  return datasets.map((ds, i) => {
    const color = ds.borderColor ?? colorForIndex(i);
    return {
      ...ds,
      borderColor: color,
      backgroundColor: ds.backgroundColor ?? color,
      pointBackgroundColor: color,
      pointBorderColor: color,
      borderWidth: ds.borderWidth ?? 2,
      tension: ds.tension ?? 0.25, // лёгкое сглаживание, опционально
    };
  });
}

export function ResultLineChart({
  datasets,
  xAxis,
  yAxis,
}: ResultLineChartProps) {
  const xLabel = formatAxisLabel(xAxis);
  const yLabel = formatAxisLabel(yAxis);

  return (
    <Line
      data={{ datasets: withColors(datasets) }}
      options={{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: true, position: 'bottom' },
        },
        scales: {
          x: {
            type: 'linear',
            beginAtZero: false,
            title: xLabel
              ? { display: true, text: xLabel }
              : { display: false },
          },
          y: {
            title: yLabel
              ? { display: true, text: yLabel }
              : { display: false },
          },
        },
      }}
    />
  );
}
