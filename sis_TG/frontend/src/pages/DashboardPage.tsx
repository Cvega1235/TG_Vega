import { useQuery } from '@tanstack/react-query';
import { getStats, getByZone, getByRating, getByCuisine, getMapData, getTopScores } from '../api/dashboard';
import StatsCards from '../components/dashboard/StatsCards';
import MapView from '../components/dashboard/MapView';
import ChartByZone from '../components/dashboard/ChartByZone';
import ChartByRating from '../components/dashboard/ChartByRating';
import ChartByCuisine from '../components/dashboard/ChartByCuisine';
import TopScoredTable from '../components/dashboard/TopScoredTable';
import ExportMenu from '../components/common/ExportMenu';

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({ queryKey: ['stats'], queryFn: getStats });
  const { data: zoneData } = useQuery({ queryKey: ['byZone'], queryFn: getByZone });
  const { data: ratingData } = useQuery({ queryKey: ['byRating'], queryFn: getByRating });
  const { data: cuisineData } = useQuery({ queryKey: ['byCuisine'], queryFn: getByCuisine });
  const { data: mapData } = useQuery({ queryKey: ['mapData'], queryFn: getMapData });
  const { data: topScores } = useQuery({ queryKey: ['topScores'], queryFn: () => getTopScores(15) });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-800">Dashboard</h2>
        <ExportMenu filters={{}} />
      </div>

      <StatsCards stats={stats} loading={isLoading} />

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
