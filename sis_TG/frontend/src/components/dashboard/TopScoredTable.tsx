import { useNavigate } from 'react-router-dom';
import type { TopScoredItem } from '../../types/dashboard';

interface Props {
  data: TopScoredItem[] | undefined;
}

export default function TopScoredTable({ data }: Props) {
  const navigate = useNavigate();

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-700">Top Clientes Potenciales</h3>
        <button
          onClick={() => navigate('/restaurants?prospecto=true&sort_by=total_score&sort_order=desc')}
          className="text-xs text-primary-600 hover:underline"
        >
          Ver todos
        </button>
      </div>

      {!data || data.length === 0 ? (
        <p className="text-gray-400 text-sm">Sin datos disponibles</p>
      ) : (
        <ul className="space-y-3">
          {data.map((item) => (
            <li
              key={item.id}
              className="flex items-center justify-between cursor-pointer group"
              onClick={() => navigate(`/restaurants/${item.id}`)}
            >
              <p className="text-sm font-medium text-gray-800 group-hover:text-primary-600 truncate pr-3">
                {item.nombre}
              </p>
              <span className={`flex-shrink-0 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold ${
                item.total_score >= 70 ? 'bg-green-100 text-green-700' :
                item.total_score >= 50 ? 'bg-yellow-100 text-yellow-700' :
                'bg-blue-100 text-blue-700'
              }`}>
                {item.total_score.toFixed(1)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
