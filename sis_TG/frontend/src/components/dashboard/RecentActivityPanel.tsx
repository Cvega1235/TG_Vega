import type { RecentSummary } from '../../types/dashboard';

interface Props {
  data: RecentSummary | undefined;
  days: number;
  onChangeDays: (days: number) => void;
}

const PERIOD_OPTIONS = [
  { label: '30 días', value: 30 },
  { label: '60 días', value: 60 },
  { label: '90 días', value: 90 },
];

export default function RecentActivityPanel({ data, days, onChangeDays }: Props) {
  const lastScraped = data?.last_scraped_at
    ? new Date(data.last_scraped_at).toLocaleString('es-BO', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
      })
    : null;

  return (
    <div className="bg-white rounded-xl shadow-sm p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-4">
        <div>
          <h3 className="text-base font-semibold text-gray-700">Actividad Reciente</h3>
          {lastScraped && (
            <p className="text-xs text-gray-400 mt-0.5">
              Último scraping: <span className="font-medium text-gray-500">{lastScraped}</span>
            </p>
          )}
        </div>
        <div className="flex gap-1.5">
          {PERIOD_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => onChangeDays(opt.value)}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                days === opt.value
                  ? 'bg-primary-600 text-white border-primary-600'
                  : 'bg-white text-gray-600 border-gray-300 hover:border-primary-400'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {data ? (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <MetricTile
            value={data.new_restaurants}
            label="Nuevos restaurantes descubiertos"
            color="text-blue-600"
            bg="bg-blue-50"
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 4v16m8-8H4" />
              </svg>
            }
          />
          <MetricTile
            value={data.new_high_score_prospects}
            label="Nuevos prospectos de alta afinidad (score ≥ 60)"
            color="text-green-600"
            bg="bg-green-50"
            alert={data.new_high_score_prospects > 0}
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
          <MetricTile
            value={data.new_clients}
            label="Restaurantes convertidos a cliente"
            color="text-purple-600"
            bg="bg-purple-50"
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            }
          />
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => <div key={i} className="h-20 rounded-lg skeleton" />)}
        </div>
      )}
    </div>
  );
}

function MetricTile({
  value, label, color, bg, icon, alert = false,
}: {
  value: number;
  label: string;
  color: string;
  bg: string;
  icon: React.ReactNode;
  alert?: boolean;
}) {
  return (
    <div className={`${bg} rounded-lg p-4 flex items-start gap-3 relative`}>
      {alert && value > 0 && (
        <span className="absolute top-2 right-2 flex h-2.5 w-2.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500" />
        </span>
      )}
      <div className={`${color} mt-0.5 flex-shrink-0`}>{icon}</div>
      <div>
        <p className={`text-2xl font-bold ${color}`}>{value}</p>
        <p className="text-xs text-gray-500 mt-0.5 leading-snug">{label}</p>
      </div>
    </div>
  );
}
