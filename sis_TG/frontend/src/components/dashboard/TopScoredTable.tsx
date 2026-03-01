import { useNavigate } from 'react-router-dom';
import type { TopScoredItem } from '../../types/dashboard';
import StatusBadge from '../common/StatusBadge';

interface Props {
  data: TopScoredItem[] | undefined;
}

function EmbutidosBadge({ value }: { value: boolean | null }) {
  if (value === null || value === undefined) return <span className="text-gray-300">—</span>;
  return value ? (
    <span className="inline-flex items-center gap-1 text-green-600 font-medium text-xs">
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
      Sí
    </span>
  ) : (
    <span className="text-gray-400 text-xs">No</span>
  );
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
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-700">Top Clientes Potenciales</h3>
        <span className="text-xs text-gray-400">Ordenado por score de afinidad</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-2 px-2 text-gray-500 font-medium">#</th>
              <th className="text-left py-2 px-2 text-gray-500 font-medium">Nombre</th>
              <th className="text-left py-2 px-2 text-gray-500 font-medium">Zona</th>
              <th className="text-left py-2 px-2 text-gray-500 font-medium">Cocina</th>
              <th className="text-left py-2 px-2 text-gray-500 font-medium">Rating</th>
              <th className="text-left py-2 px-2 text-gray-500 font-medium">Estado</th>
              <th className="text-center py-2 px-2 text-gray-500 font-medium">Embutidos</th>
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
                <td className="py-2 px-2 text-gray-600">{item.zona || '—'}</td>
                <td className="py-2 px-2 text-gray-500 max-w-[120px] truncate">{item.tipo_cocina || '—'}</td>
                <td className="py-2 px-2 text-gray-600">
                  {item.rating ? (
                    <span className="flex items-center gap-1">
                      <svg className="w-3 h-3 text-yellow-400 fill-yellow-400" viewBox="0 0 24 24">
                        <path d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                      </svg>
                      {item.rating}
                    </span>
                  ) : '—'}
                </td>
                <td className="py-2 px-2">
                  <StatusBadge status={item.status} />
                </td>
                <td className="py-2 px-2 text-center">
                  <EmbutidosBadge value={item.tiene_embutidos} />
                </td>
                <td className="py-2 px-2 text-right">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold ${
                    item.total_score >= 70 ? 'bg-green-100 text-green-700' :
                    item.total_score >= 50 ? 'bg-yellow-100 text-yellow-700' :
                    'bg-blue-100 text-blue-700'
                  }`}>
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
