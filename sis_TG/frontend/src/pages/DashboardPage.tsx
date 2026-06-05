import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getStats, getByZone, getByRating, getByCuisine, getBySource, getMapData, getTopScores, getClientHistory, getRecentSummary, getKpiEvolution } from '../api/dashboard';
import StatsCards from '../components/dashboard/StatsCards';
import MapView from '../components/dashboard/MapView';
import ChartByZone from '../components/dashboard/ChartByZone';
import ChartByRating from '../components/dashboard/ChartByRating';
import ChartByCuisine from '../components/dashboard/ChartByCuisine';
import TopScoredTable from '../components/dashboard/TopScoredTable';
import ClientHistorySection from '../components/dashboard/ClientHistorySection';
import KpiEvolutionSection from '../components/dashboard/KpiEvolutionSection';
import RecentActivityPanel from '../components/dashboard/RecentActivityPanel';
import ExportMenu from '../components/common/ExportMenu';

export default function DashboardPage() {
  const [selectedFuente, setSelectedFuente] = useState<string | null>(null);
  const [selectedDays, setSelectedDays] = useState(30);

  const fuente = selectedFuente ?? undefined;

  const { data: sources } = useQuery({ queryKey: ['bySource'], queryFn: getBySource });
  const { data: stats, isLoading } = useQuery({ queryKey: ['stats', fuente], queryFn: () => getStats(fuente) });
  const { data: zoneData } = useQuery({ queryKey: ['byZone', fuente], queryFn: () => getByZone(fuente) });
  const { data: ratingData } = useQuery({ queryKey: ['byRating', fuente], queryFn: () => getByRating(fuente) });
  const { data: cuisineData } = useQuery({ queryKey: ['byCuisine', fuente], queryFn: () => getByCuisine(fuente) });
  const { data: mapData } = useQuery({ queryKey: ['mapData'], queryFn: getMapData });
  const { data: topScores } = useQuery({ queryKey: ['topScores'], queryFn: () => getTopScores(15) });
  const { data: clientHistory } = useQuery({ queryKey: ['clientHistory'], queryFn: getClientHistory });
  const { data: kpiEvolution } = useQuery({ queryKey: ['kpiEvolution'], queryFn: getKpiEvolution });
  const { data: recentSummary } = useQuery({
    queryKey: ['recentSummary', selectedDays],
    queryFn: () => getRecentSummary(selectedDays),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-800">Dashboard</h2>
        <ExportMenu filters={{}} />
      </div>

      {sources && sources.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-gray-500 font-medium">Fuente:</span>
          <button
            onClick={() => setSelectedFuente(null)}
            className={`text-xs px-3 py-1 rounded-full border transition-colors ${
              !selectedFuente
                ? 'bg-primary-600 text-white border-primary-600'
                : 'bg-white text-gray-600 border-gray-300 hover:border-primary-400'
            }`}
          >
            Todas
          </button>
          {sources.filter((s) => s.label !== 'manual').map((s) => (
            <button
              key={s.label}
              onClick={() => setSelectedFuente(s.label === selectedFuente ? null : s.label)}
              className={`text-xs px-3 py-1 rounded-full border transition-colors ${
                selectedFuente === s.label
                  ? 'bg-primary-600 text-white border-primary-600'
                  : 'bg-white text-gray-600 border-gray-300 hover:border-primary-400'
              }`}
            >
              {s.label}
              <span className="ml-1.5 opacity-60">({s.value})</span>
            </button>
          ))}
        </div>
      )}

      <StatsCards stats={stats} loading={isLoading} />

      <RecentActivityPanel
        data={recentSummary}
        days={selectedDays}
        onChangeDays={setSelectedDays}
      />

      <ClientHistorySection data={clientHistory} />

      <KpiEvolutionSection data={kpiEvolution} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <MapView data={mapData} />
        <ChartByZone data={zoneData} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartByRating data={ratingData} />
        <ChartByCuisine data={cuisineData} />
      </div>

      <TopScoredTable data={topScores} />
    </div>
  );
}
