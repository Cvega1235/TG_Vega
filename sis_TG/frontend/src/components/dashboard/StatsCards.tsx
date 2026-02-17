import type { DashboardStats } from '../../types/dashboard';

interface Props {
  stats: DashboardStats | undefined;
  loading: boolean;
}

export default function StatsCards({ stats, loading }: Props) {
  if (loading || !stats) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white rounded-xl p-5 shadow-sm animate-pulse h-24" />
        ))}
      </div>
    );
  }

  const cards = [
    {
      title: 'Total Restaurantes',
      value: stats.total_restaurants,
      color: 'text-primary-600',
      bg: 'bg-primary-50',
    },
    {
      title: 'Rating Promedio',
      value: stats.avg_rating ? stats.avg_rating.toFixed(1) : 'N/A',
      color: 'text-yellow-600',
      bg: 'bg-yellow-50',
    },
    {
      title: 'Con Coordenadas',
      value: stats.total_with_coordinates,
      color: 'text-green-600',
      bg: 'bg-green-50',
    },
    {
      title: 'Con Telefono',
      value: stats.total_with_phone,
      color: 'text-purple-600',
      bg: 'bg-purple-50',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <div key={card.title} className={`${card.bg} rounded-xl p-5 shadow-sm`}>
          <p className="text-sm text-gray-600">{card.title}</p>
          <p className={`text-2xl font-bold mt-1 ${card.color}`}>{card.value}</p>
        </div>
      ))}
    </div>
  );
}
