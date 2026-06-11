import { useQuery } from '@tanstack/react-query';
import { getByZone, getMapData, getTopScores, getClientHistory, getKpiEvolution } from '../api/dashboard';
import MapView from '../components/dashboard/MapView';
import ChartByZone from '../components/dashboard/ChartByZone';
import TopScoredTable from '../components/dashboard/TopScoredTable';
import ClientHistorySection from '../components/dashboard/ClientHistorySection';
import KpiEvolutionSection from '../components/dashboard/KpiEvolutionSection';
import ExportMenu from '../components/common/ExportMenu';

export default function DashboardPage() {
  const { data: zoneData } = useQuery({ queryKey: ['byZone'], queryFn: () => getByZone() });
  const { data: mapData } = useQuery({ queryKey: ['mapData'], queryFn: getMapData });
  const { data: topScores } = useQuery({ queryKey: ['topScores'], queryFn: () => getTopScores(6) });
  const { data: clientHistory } = useQuery({ queryKey: ['clientHistory'], queryFn: getClientHistory });
  const { data: kpiEvolution } = useQuery({ queryKey: ['kpiEvolution', 'v2'], queryFn: getKpiEvolution, staleTime: 0 });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-800">Dashboard</h2>
        <ExportMenu filters={{}} />
      </div>

      <KpiEvolutionSection data={kpiEvolution} />

      <ClientHistorySection data={clientHistory} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <MapView data={mapData} />
        <ChartByZone data={zoneData} />
      </div>

      <TopScoredTable data={topScores} />
    </div>
  );
}
