import { useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { ClientHistoryData } from '../../types/dashboard';

interface Props {
  data: ClientHistoryData | undefined;
}

export default function ClientHistorySection({ data }: Props) {
  const navigate = useNavigate();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 bg-white rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-gray-700">Nuevos Clientes por Mes (últimos 12 meses)</h3>
          {data && (
            <span className="text-xs text-gray-400">
              {data.new_this_month > 0
                ? `+${data.new_this_month} este mes`
                : 'Sin conversiones este mes'}
            </span>
          )}
        </div>

        {!data || data.monthly.length === 0 ? (
          <p className="text-gray-400 text-sm">Sin datos de conversiones disponibles</p>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data.monthly}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" tick={{ fontSize: 11 }} angle={-30} textAnchor="end" height={60} />
              <YAxis allowDecimals={false} />
              <Tooltip formatter={(value: number) => [value, 'Nuevos clientes']} />
              <Bar dataKey="count" fill="#9B1C2E" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="bg-white rounded-xl p-5 shadow-sm flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-gray-700">Conversiones Recientes</h3>
          <button
            onClick={() => navigate('/restaurants?status=cliente')}
            className="text-xs text-primary-600 hover:underline"
          >
            Ver todos
          </button>
        </div>

        {!data || data.recent_conversions.length === 0 ? (
          <p className="text-gray-400 text-sm">Sin conversiones registradas</p>
        ) : (
          <ul className="space-y-3 flex-1">
            {data.recent_conversions.map((r) => (
              <li
                key={r.id}
                className="cursor-pointer group"
                onClick={() => navigate(`/restaurants/${r.id}`)}
              >
                <p className="text-sm font-medium text-gray-800 group-hover:text-primary-600 truncate">
                  {r.nombre}
                </p>
                <div className="flex items-center gap-2 mt-0.5">
                  {r.zona && <span className="text-xs text-gray-400">{r.zona}</span>}
                  <span className="text-xs text-gray-300">·</span>
                  <span className="text-xs text-gray-400">
                    {new Date(r.converted_at).toLocaleDateString('es-ES', {
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric',
                    })}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}

        {data && (
          <div className="mt-4 pt-4 border-t border-gray-100 text-center">
            <p className="text-2xl font-bold text-primary-700">{data.total_clients}</p>
            <p className="text-xs text-gray-400 mt-0.5">clientes totales</p>
          </div>
        )}
      </div>
    </div>
  );
}
