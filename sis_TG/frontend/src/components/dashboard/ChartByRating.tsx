import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import type { ChartDataPoint } from '../../types/dashboard';

interface Props {
  data: ChartDataPoint[] | undefined;
}

const COLORS = ['#4A0B0B', '#7F1D1D', '#9B1C2E', '#C94B6A', '#FF8FA3'];

export default function ChartByRating({ data }: Props) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-medium text-gray-700 mb-4">Distribucion de Rating</h3>
        <p className="text-gray-400 text-sm">Sin datos disponibles</p>
      </div>
    );
  }

  const filtered = data.filter((d) => d.value > 0);

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm">
      <h3 className="text-sm font-medium text-gray-700 mb-4">Distribucion de Rating</h3>
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={filtered}
            dataKey="value"
            nameKey="label"
            cx="50%"
            cy="50%"
            outerRadius={80}
            label={({ label, value }) => `${label}: ${value}`}
          >
            {filtered.map((_, index) => (
              <Cell key={index} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
