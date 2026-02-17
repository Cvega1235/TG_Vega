import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  PieChart, Pie, Cell, ResponsiveContainer, Legend,
} from 'recharts';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { useNavigate } from 'react-router-dom';
import {
  getStats, getByZone, getByStatus, getByCuisine, getByRating, getMapData,
} from '../api/dashboard';
import ExportMenu from '../components/common/ExportMenu';
import type { MapDataPoint } from '../types/dashboard';

const COLORS = ['#2563eb', '#16a34a', '#eab308', '#ef4444', '#8b5cf6',
  '#06b6d4', '#f97316', '#ec4899', '#14b8a6', '#6366f1'];

const STATUS_LABELS: Record<string, string> = {
  nuevo: 'Nuevo',
  contactado: 'Contactado',
  interesado: 'Interesado',
  cliente: 'Cliente',
  no_interesado: 'No Interesado',
};

const FUNNEL_ORDER = ['nuevo', 'contactado', 'interesado', 'cliente'];

function getScoreColor(score: number | null): string {
  if (score === null || score === undefined) return '#9ca3af';
  if (score >= 70) return '#22c55e';
  if (score >= 50) return '#eab308';
  return '#ef4444';
}

function createScoreIcon(score: number | null) {
  const color = getScoreColor(score);
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="background:${color};width:12px;height:12px;border-radius:50%;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.3)"></div>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  });
}

export default function ReportsPage() {
  const navigate = useNavigate();

  const { data: stats, isLoading } = useQuery({ queryKey: ['stats'], queryFn: getStats });
  const { data: zoneData } = useQuery({ queryKey: ['byZone'], queryFn: getByZone });
  const { data: statusData } = useQuery({ queryKey: ['byStatus'], queryFn: getByStatus });
  const { data: cuisineData } = useQuery({ queryKey: ['byCuisine'], queryFn: getByCuisine });
  const { data: ratingData } = useQuery({ queryKey: ['byRating'], queryFn: getByRating });
  const { data: mapData } = useQuery({ queryKey: ['mapData'], queryFn: getMapData });

  // Source data from stats
  const sourceChartData = useMemo(() => {
    if (!stats?.source_counts) return [];
    return Object.entries(stats.source_counts).map(([label, value]) => ({ label, value }));
  }, [stats]);

  // Funnel data
  const funnelData = useMemo(() => {
    if (!statusData) return [];
    return FUNNEL_ORDER.map((status, idx) => {
      const count = statusData.find(d => d.label === status)?.value || 0;
      const prevCount = idx > 0
        ? (statusData.find(d => d.label === FUNNEL_ORDER[idx - 1])?.value || 1)
        : count;
      return {
        status,
        label: STATUS_LABELS[status],
        count,
        conversionRate: idx === 0 ? 100 : (prevCount > 0 ? (count / prevCount) * 100 : 0),
      };
    });
  }, [statusData]);

  const noInteresadoCount = statusData?.find(d => d.label === 'no_interesado')?.value || 0;
  const maxFunnelCount = funnelData.length > 0 ? funnelData[0].count : 1;

  // Zone scores from map data
  const zoneScores = useMemo(() => {
    if (!mapData) return [];
    const zones: Record<string, { total: number; scoreSum: number; scoreCount: number }> = {};
    for (const point of mapData) {
      const zona = 'Sin zona'; // mapData doesn't have zona, we'll use zoneData for counts
      if (point.total_score !== null) {
        // Group points roughly - we'll show zone data from zoneData instead
      }
    }
    // Better approach: use zoneData for counts, and compute avg scores per zone from map data
    // Since mapData doesn't include zona, we use zoneData directly
    return [];
  }, [mapData]);

  // Top 10 cuisine data
  const top10Cuisine = useMemo(() => {
    if (!cuisineData) return [];
    return [...cuisineData].sort((a, b) => b.value - a.value).slice(0, 10);
  }, [cuisineData]);

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Reportes</h2>
          <p className="text-gray-500 mt-1">Analisis integral del mercado de restaurantes</p>
        </div>
        <ExportMenu filters={{}} />
      </div>

      {/* ============================================ */}
      {/* SECCION 1: RESUMEN GENERAL                   */}
      {/* ============================================ */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2">Resumen General</h3>

        {/* Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-primary-50 rounded-xl p-5 shadow-sm">
            <p className="text-sm text-gray-600">Total Restaurantes</p>
            <p className="text-2xl font-bold mt-1 text-primary-600">{stats?.total_restaurants || 0}</p>
          </div>
          <div className="bg-yellow-50 rounded-xl p-5 shadow-sm">
            <p className="text-sm text-gray-600">Rating Promedio</p>
            <p className="text-2xl font-bold mt-1 text-yellow-600">
              {stats?.avg_rating ? stats.avg_rating.toFixed(1) : 'N/A'}
            </p>
          </div>
          <div className="bg-green-50 rounded-xl p-5 shadow-sm">
            <p className="text-sm text-gray-600">Con Coordenadas</p>
            <p className="text-2xl font-bold mt-1 text-green-600">{stats?.total_with_coordinates || 0}</p>
          </div>
          <div className="bg-purple-50 rounded-xl p-5 shadow-sm">
            <p className="text-sm text-gray-600">Con Telefono</p>
            <p className="text-2xl font-bold mt-1 text-purple-600">{stats?.total_with_phone || 0}</p>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* By Zone */}
          <div className="bg-white rounded-xl p-5 shadow-sm">
            <h4 className="text-sm font-medium text-gray-700 mb-4">Restaurantes por Zona</h4>
            {zoneData && zoneData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={zoneData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#2563eb" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-400 text-center py-8">Sin datos</p>
            )}
          </div>

          {/* By Source */}
          <div className="bg-white rounded-xl p-5 shadow-sm">
            <h4 className="text-sm font-medium text-gray-700 mb-4">Distribucion por Fuente</h4>
            {sourceChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={sourceChartData}
                    dataKey="value"
                    nameKey="label"
                    cx="50%"
                    cy="50%"
                    outerRadius={90}
                    label={({ label, percent }) => `${label} (${(percent * 100).toFixed(0)}%)`}
                  >
                    {sourceChartData.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-400 text-center py-8">Sin datos</p>
            )}
          </div>

          {/* By Cuisine (Top 10) */}
          <div className="bg-white rounded-xl p-5 shadow-sm">
            <h4 className="text-sm font-medium text-gray-700 mb-4">Top 10 Tipos de Cocina</h4>
            {top10Cuisine.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={top10Cuisine}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#16a34a" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-400 text-center py-8">Sin datos</p>
            )}
          </div>

          {/* By Rating */}
          <div className="bg-white rounded-xl p-5 shadow-sm">
            <h4 className="text-sm font-medium text-gray-700 mb-4">Distribucion por Rating</h4>
            {ratingData && ratingData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={ratingData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="label" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#eab308" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-400 text-center py-8">Sin datos</p>
            )}
          </div>
        </div>
      </div>

      {/* ============================================ */}
      {/* SECCION 2: EMBUDO DE VENTAS                  */}
      {/* ============================================ */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2">Embudo de Ventas</h3>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Funnel Visual */}
          <div className="bg-white rounded-xl p-5 shadow-sm">
            <h4 className="text-sm font-medium text-gray-700 mb-4">Progresion de Estados</h4>
            <div className="space-y-3">
              {funnelData.map((stage, idx) => {
                const widthPct = maxFunnelCount > 0 ? (stage.count / maxFunnelCount) * 100 : 0;
                const colors = ['#3b82f6', '#8b5cf6', '#eab308', '#22c55e'];
                return (
                  <div key={stage.status}>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="font-medium text-gray-700">{stage.label}</span>
                      <span className="text-gray-500">{stage.count}</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-8 flex items-center">
                      <div
                        className="h-8 rounded-full transition-all flex items-center justify-center text-white text-xs font-bold"
                        style={{
                          width: `${Math.max(widthPct, 5)}%`,
                          backgroundColor: colors[idx],
                        }}
                      >
                        {widthPct >= 15 ? stage.count : ''}
                      </div>
                    </div>
                    {idx < funnelData.length - 1 && (
                      <div className="text-center text-gray-400 text-xs my-1">
                        ↓
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Conversion Metrics */}
          <div className="bg-white rounded-xl p-5 shadow-sm">
            <h4 className="text-sm font-medium text-gray-700 mb-4">Metricas de Conversion</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Etapa</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Cantidad</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Conv. desde anterior</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {funnelData.map((stage, idx) => (
                    <tr key={stage.status} className="hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium">{stage.label}</td>
                      <td className="py-3 px-4 text-right">{stage.count}</td>
                      <td className="py-3 px-4 text-right">
                        {idx === 0 ? (
                          <span className="text-gray-400">-</span>
                        ) : (
                          <span className={stage.conversionRate >= 50 ? 'text-green-600 font-semibold' : 'text-orange-500 font-semibold'}>
                            {stage.conversionRate.toFixed(1)}%
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* No Interesado */}
            <div className="mt-4 bg-red-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-red-700">No Interesado</span>
                <span className="text-lg font-bold text-red-600">{noInteresadoCount}</span>
              </div>
              {stats && stats.total_restaurants > 0 && (
                <p className="text-xs text-red-500 mt-1">
                  {((noInteresadoCount / stats.total_restaurants) * 100).toFixed(1)}% del total
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ============================================ */}
      {/* SECCION 3: ANALISIS GEOGRAFICO               */}
      {/* ============================================ */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2">Analisis Geografico</h3>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Restaurants by Zone (horizontal bar) */}
          <div className="bg-white rounded-xl p-5 shadow-sm">
            <h4 className="text-sm font-medium text-gray-700 mb-4">Restaurantes por Zona</h4>
            {zoneData && zoneData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={[...zoneData].sort((a, b) => b.value - a.value).slice(0, 10)} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis type="category" dataKey="label" width={120} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#2563eb" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-400 text-center py-8">Sin datos</p>
            )}
          </div>

          {/* Zone Table */}
          <div className="bg-white rounded-xl p-5 shadow-sm">
            <h4 className="text-sm font-medium text-gray-700 mb-4">Detalle por Zona</h4>
            {zoneData && zoneData.length > 0 ? (
              <div className="overflow-x-auto max-h-[300px] overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="text-left py-2 px-3 font-medium text-gray-600">Zona</th>
                      <th className="text-right py-2 px-3 font-medium text-gray-600">Restaurantes</th>
                      <th className="text-right py-2 px-3 font-medium text-gray-600">% del Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {[...zoneData].sort((a, b) => b.value - a.value).map((zone) => (
                      <tr key={zone.label} className="hover:bg-gray-50">
                        <td className="py-2 px-3 font-medium">{zone.label}</td>
                        <td className="py-2 px-3 text-right">{zone.value}</td>
                        <td className="py-2 px-3 text-right text-gray-500">
                          {stats ? ((zone.value / stats.total_restaurants) * 100).toFixed(1) : 0}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-gray-400 text-center py-8">Sin datos</p>
            )}
          </div>
        </div>

        {/* Map with Score Colors */}
        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h4 className="text-sm font-medium text-gray-700 mb-4">Mapa de Scores</h4>
          <div className="h-[400px] rounded-lg overflow-hidden">
            <MapContainer
              center={[-16.5, -68.15]}
              zoom={13}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {mapData?.map((point) => (
                <Marker
                  key={point.id}
                  position={[point.latitud, point.longitud]}
                  icon={createScoreIcon(point.total_score)}
                >
                  <Popup>
                    <div className="text-sm">
                      <p className="font-semibold">{point.nombre}</p>
                      {point.rating && <p>Rating: {point.rating}/5</p>}
                      <p>Score: {point.total_score !== null ? point.total_score.toFixed(1) : 'Sin score'}</p>
                      <button
                        onClick={() => navigate(`/restaurants/${point.id}`)}
                        className="text-primary-500 hover:underline mt-1 block"
                      >
                        Ver detalle
                      </button>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
          <div className="flex gap-4 mt-3 text-xs text-gray-500">
            <div className="flex items-center gap-1">
              <div style={{ background: '#ef4444', width: 10, height: 10, borderRadius: '50%' }} />
              <span>Score &lt;50</span>
            </div>
            <div className="flex items-center gap-1">
              <div style={{ background: '#eab308', width: 10, height: 10, borderRadius: '50%' }} />
              <span>Score 50-70</span>
            </div>
            <div className="flex items-center gap-1">
              <div style={{ background: '#22c55e', width: 10, height: 10, borderRadius: '50%' }} />
              <span>Score 70+</span>
            </div>
            <div className="flex items-center gap-1">
              <div style={{ background: '#9ca3af', width: 10, height: 10, borderRadius: '50%' }} />
              <span>Sin score</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
