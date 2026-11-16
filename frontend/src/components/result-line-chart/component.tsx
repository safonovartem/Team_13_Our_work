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
}

export function ResultLineChart({ datasets }: ResultLineChartProps) {
  return (
    <Line
      data={{
        datasets,
      }}
      options={{
        scales: {
          x: {
            beginAtZero: false,
            type: 'linear',
          },
        },
      }}
    />
  );
}
