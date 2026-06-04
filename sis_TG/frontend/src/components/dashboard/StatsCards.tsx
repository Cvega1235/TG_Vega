import { useNavigate } from 'react-router-dom';
import type { DashboardStats } from '../../types/dashboard';

interface Props {
  stats: DashboardStats | undefined;
  loading: boolean;
}

interface CardDef {
  title: string;
  value: string | number;
  color: string;
  bg: string;
  iconBg: string;
  icon: React.ReactNode;
  link: string;
}

const IconStore = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
  </svg>
);
const IconTarget = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);
const IconUsers = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);
const IconSausage = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
  </svg>
);
const IconBell = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
  </svg>
);
const IconStar = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
  </svg>
);

function StatCard({ title, value, color, bg, iconBg, icon, link, delay }: CardDef & { delay: number }) {
  const navigate = useNavigate();

  return (
    <button
      onClick={() => navigate(link)}
      className={`${bg} rounded-xl p-5 shadow-sm flex items-center gap-4 card-hover animate-fade-in w-full text-left
        hover:shadow-md hover:scale-[1.02] transition-all duration-200 cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary-300`}
      style={{ animationDelay: `${delay}s` }}
    >
      <div className={`${iconBg} rounded-lg p-3 ${color} flex-shrink-0`}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-gray-500 font-medium uppercase tracking-wide leading-tight">{title}</p>
        <p className={`text-2xl font-bold mt-1 ${color}`}>{value}</p>
      </div>
      <svg className="w-4 h-4 text-gray-300 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
      </svg>
    </button>
  );
}

export default function StatsCards({ stats, loading }: Props) {
  if (loading || !stats) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="rounded-xl p-5 shadow-sm h-24 skeleton" />
        ))}
      </div>
    );
  }

  const cards: CardDef[] = [
    {
      title: 'Tasa de Conversión',
      value: `${stats.conversion_rate}%`,
      color: 'text-green-700',
      bg: 'bg-green-50',
      iconBg: 'bg-green-100',
      icon: <IconTarget />,
      link: '/restaurants?status=cliente',
    },
    {
      title: 'Alta Afinidad (Score ≥ 70)',
      value: stats.high_affinity_count,
      color: 'text-primary-600',
      bg: 'bg-primary-50',
      iconBg: 'bg-primary-100',
      icon: <IconStar />,
      link: '/restaurants?min_score=70&sort_by=total_score&sort_order=desc',
    },
    {
      title: 'Clientes Actuales',
      value: stats.clients_count,
      color: 'text-purple-700',
      bg: 'bg-purple-50',
      iconBg: 'bg-purple-100',
      icon: <IconUsers />,
      link: '/restaurants?status=cliente',
    },
    {
      title: 'Restaurantes en Seguimiento',
      value: stats.in_followup_count,
      color: 'text-orange-700',
      bg: 'bg-orange-50',
      iconBg: 'bg-orange-100',
      icon: <IconSausage />,
      link: '/restaurants?status=contactado',
    },
    {
      title: 'Prospectos a Contactar',
      value: stats.to_contact_count,
      color: 'text-primary-700',
      bg: 'bg-primary-50',
      iconBg: 'bg-primary-100',
      icon: <IconBell />,
      link: '/restaurants?prospecto=true&sort_by=total_score&sort_order=desc',
    },
    {
      title: 'Nuevos Clientes Este Mes',
      value: stats.new_clients_this_month,
      color: 'text-yellow-700',
      bg: 'bg-yellow-50',
      iconBg: 'bg-yellow-100',
      icon: <IconStore />,
      link: '/restaurants?status=cliente',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {cards.map((card, i) => (
        <StatCard key={card.title} {...card} delay={i * 0.07} />
      ))}
    </div>
  );
}
