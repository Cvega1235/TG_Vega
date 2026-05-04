import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { ChartDataPoint } from '../../types/dashboard';

interface Props {
  data: ChartDataPoint[] | undefined;
}

export default function ChartByZone({ data }: Props) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-medium text-gray-700 mb-4">Restaurantes por Zona</h3>
        <p className="text-gray-400 text-sm">Sin datos disponibles</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm">
      <h3 className="text-sm font-medium text-gray-700 mb-4">Restaurantes por Zona</h3>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="label" tick={{ fontSize: 11 }} angle={-30} textAnchor="end" height={60} />
          <YAxis />
          <Tooltip />
          <Bar dataKey="value" fill="#9B1C2E" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
