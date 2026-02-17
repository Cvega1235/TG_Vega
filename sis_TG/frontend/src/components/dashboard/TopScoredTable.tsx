import { useNavigate } from 'react-router-dom';
import type { TopScoredItem } from '../../types/dashboard';
import StatusBadge from '../common/StatusBadge';

interface Props {
  data: TopScoredItem[] | undefined;
}

export default function TopScoredTable({ data }: Props) {
  const navigate = useNavigate();

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-medium text-gray-700 mb-4">Top Clientes Potenciales</h3>
        <p className="text-gray-400 text-sm">Sin datos disponibles</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm">
      <h3 className="text-sm font-medium text-gray-700 mb-4">Top Clientes Potenciales</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-2 px-2 text-gray-500 font-medium">#</th>
              <th className="text-left py-2 px-2 text-gray-500 font-medium">Nombre</th>
              <th className="text-left py-2 px-2 text-gray-500 font-medium">Zona</th>
              <th className="text-left py-2 px-2 text-gray-500 font-medium">Rating</th>
              <th className="text-left py-2 px-2 text-gray-500 font-medium">Estado</th>
              <th className="text-right py-2 px-2 text-gray-500 font-medium">Score</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item, idx) => (
              <tr
                key={item.id}
                className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
                onClick={() => navigate(`/restaurants/${item.id}`)}
              >
                <td className="py-2 px-2 text-gray-400">{idx + 1}</td>
                <td className="py-2 px-2 font-medium text-gray-800">{item.nombre}</td>
                <td className="py-2 px-2 text-gray-600">{item.zona || '-'}</td>
                <td className="py-2 px-2 text-gray-600">
                  {item.rating ? `${item.rating}/5` : '-'}
                </td>
                <td className="py-2 px-2">
                  <StatusBadge status={item.status} />
                </td>
                <td className="py-2 px-2 text-right">
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-primary-100 text-primary-700">
                    {item.total_score.toFixed(1)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
