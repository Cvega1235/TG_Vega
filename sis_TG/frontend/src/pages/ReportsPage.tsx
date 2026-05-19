import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  PieChart, Pie, Cell, ResponsiveContainer,
  AreaChart, Area,
} from 'recharts';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { useNavigate } from 'react-router-dom';
import {
  getStats, getByZone, getByStatus, getByCuisine, getByRating, getMapData, getTopProspects,
} from '../api/dashboard';
import ExportMenu from '../components/common/ExportMenu';
import type { MapDataPoint, TopProspect } from '../types/dashboard';

const COLORS = ['#9B1C2E', '#16a34a', '#eab308', '#ef4444', '#8b5cf6',
  '#06b6d4', '#f97316', '#ec4899', '#14b8a6', '#6366f1'];

const STATUS_LABELS: Record<string, string> = {
  nuevo: 'Nuevo',
  contactado: 'Contactado',
  interesado: 'Interesado',
  cliente: 'Cliente',
  no_interesado: 'No Interesado',
};

const STATUS_COLORS: Record<string, string> = {
  nuevo: 'bg-blue-100 text-blue-700',
  contactado: 'bg-yellow-100 text-yellow-700',
  interesado: 'bg-orange-100 text-orange-700',
};

const FUNNEL_ORDER = ['nuevo', 'contactado', 'interesado', 'cliente'];
const RANK_MEDALS = ['🥇', '🥈', '🥉'];
const RANK_BORDERS = ['border-yellow-300 bg-gradient-to-br from-yellow-50 to-white', 'border-gray-300 bg-gradient-to-br from-gray-50 to-white', 'border-amber-700/30 bg-gradient-to-br from-amber-50 to-white'];
const RANK_SCORE_COLORS = ['text-yellow-600', 'text-gray-500', 'text-amber-700'];

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

function getReasons(p: TopProspect): string[] {
  const reasons: string[] = [];
  if ((p.cuisine_score ?? 0) >= 20) reasons.push('Alta afinidad de productos con el catálogo Don Piotr');
  if ((p.rating_score ?? 0) >= 15) reasons.push('Rating excepcional entre los restaurantes del mercado');
  if ((p.reviews_score ?? 0) >= 10) reasons.push('Alto volumen de reseñas indica establecimiento consolidado');
  if ((p.zone_score ?? 0) >= 10) reasons.push('Ubicado en zona de alto potencial comercial');
  if (p.tiene_embutidos) reasons.push('Menú con productos afines a embutidos detectado');
  if (reasons.length === 0) reasons.push('Score compuesto elevado según análisis ML del sistema');
  return reasons.slice(0, 3);
}

function ProspectCard({ prospect, rank }: { prospect: TopProspect; rank: number }) {
  const navigate = useNavigate();
  const reasons = getReasons(prospect);
  const scorePct = Math.min(prospect.total_score, 100);

  return (
    <div className={`rounded-2xl border-2 p-5 shadow-sm flex flex-col gap-4 h-full ${RANK_BORDERS[rank]}`}>
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{RANK_MEDALS[rank]}</span>
          <div>
            <p className="font-bold text-gray-800 text-base leading-tight">{prospect.nombre}</p>
            <p className="text-xs text-gray-500 mt-0.5">
              {prospect.zona ?? 'Sin zona'} {prospect.tipo_cocina ? `· ${prospect.tipo_cocina}` : ''}
            </p>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_COLORS[prospect.status] ?? 'bg-gray-100 text-gray-600'}`}>
            {STATUS_LABELS[prospect.status] ?? prospect.status}
          </span>
          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
            prospect.score_source === 'ml'
              ? 'bg-blue-50 text-blue-600 border-blue-200'
              : 'bg-gray-50 text-gray-400 border-gray-200'
          }`}>
            {prospect.score_source === 'ml' ? 'Score ML' : 'Score ICP'}
          </span>
        </div>
      </div>

      {/* Score ring + stats */}
      <div className="flex items-center gap-4">
        <div className="relative flex items-center justify-center w-20 h-20 flex-shrink-0">
          <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
            <circle cx="40" cy="40" r="34" fill="none" stroke="#f3f4f6" strokeWidth="8" />
            <circle
              cx="40" cy="40" r="34" fill="none"
              stroke={getScoreColor(prospect.total_score)}
              strokeWidth="8"
              strokeDasharray={`${(scorePct / 100) * 213.6} 213.6`}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute text-center">
            <p className={`text-lg font-bold leading-none ${RANK_SCORE_COLORS[rank]}`}>
              {prospect.total_score.toFixed(0)}
            </p>
            <p className="text-[10px] text-gray-400">/100</p>
          </div>
        </div>
        <div className="space-y-1 text-sm">
          {prospect.rating && (
            <p className="flex items-center gap-1 text-gray-600">
              <span className="text-yellow-500">★</span>
              <span className="font-medium">{prospect.rating.toFixed(1)}</span>
              <span className="text-gray-400">/ 5</span>
            </p>
          )}
          {prospect.telefono && (
            <p className="text-gray-500 text-xs">📞 Teléfono disponible</p>
          )}
          {prospect.tiene_embutidos && (
            <p className="text-green-600 text-xs font-medium">✓ Usa embutidos</p>
          )}
        </div>
      </div>

      {/* Reasons */}
      <div className="flex-1 bg-white/70 rounded-xl p-3 space-y-1.5 border border-gray-100">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
          Por qué el sistema lo recomienda
        </p>
        {reasons.map((r, i) => (
          <p key={i} className="text-xs text-gray-600 flex items-start gap-1.5">
            <span className="text-green-500 mt-0.5 flex-shrink-0">✓</span>
            {r}
          </p>
        ))}
      </div>

      <button
        onClick={() => navigate(`/restaurants/${prospect.id}`)}
        className="w-full py-2 rounded-xl text-sm font-semibold text-white transition-all"
        style={{ background: 'linear-gradient(90deg,#7F1D1D,#9B1C2E)' }}
      >
        Ver prospecto →
      </button>
    </div>
  );
}

export default function ReportsPage() {
  const navigate = useNavigate();

  const { data: stats, isLoading } = useQuery({ queryKey: ['stats'], queryFn: getStats });
  const { data: zoneData } = useQuery({ queryKey: ['byZone'], queryFn: getByZone });
  const { data: statusData } = useQuery({ queryKey: ['byStatus'], queryFn: getByStatus });
  const { data: cuisineData } = useQuery({ queryKey: ['byCuisine'], queryFn: getByCuisine });
  const { data: ratingData } = useQuery({ queryKey: ['byRating'], queryFn: getByRating });
  const { data: mapData } = useQuery({ queryKey: ['mapData'], queryFn: getMapData });
  const { data: topProspects } = useQuery({ queryKey: ['topProspects'], queryFn: () => getTopProspects(3) });

  const sourceChartData = useMemo(() => {
    if (!stats?.source_counts) return [];
    return Object.entries(stats.source_counts).map(([label, value]) => ({ label, value }));
  }, [stats]);

  const funnelData = useMemo(() => {
    if (!statusData) return [];
    return FUNNEL_ORDER.map((status, idx) => {
      const count = statusData.find(d => d.label === status)?.value || 0;
      const prevCount = idx > 0
        ? (statusData.find(d => d.label === FUNNEL_ORDER[idx - 1])?.value ?? 0)
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
  const top10Cuisine = useMemo(() => {
    if (!cuisineData) return [];
    return [...cuisineData].sort((a, b) => b.value - a.value).slice(0, 10);
  }, [cuisineData]);

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <div className="space-y-10">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Reportes</h2>
          <p className="text-gray-500 mt-1 text-sm">Análisis integral del mercado de restaurantes en La Paz</p>
        </div>
        <ExportMenu filters={{}} />
      </div>

      {/* ============================================ */}
      {/* SECCIÓN 1: RECOMENDACIONES DEL SISTEMA       */}
      {/* ============================================ */}
      <div>
        <div className="flex items-center gap-3 mb-1">
          <h3 className="text-lg font-bold text-gray-800">Recomendaciones del Sistema</h3>
          <span className="text-xs bg-primary-100 text-primary-700 font-semibold px-2 py-0.5 rounded-full">
            Análisis ML
          </span>
        </div>
        <p className="text-sm text-gray-500 mb-5">
          Los 3 restaurantes con mayor potencial de conversión según el modelo de inteligencia de mercado,
          excluyendo clientes actuales y prospectos descartados.
        </p>

        {topProspects && topProspects.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 items-stretch">
            {topProspects.map((p, i) => (
              <ProspectCard key={p.id} prospect={p} rank={i} />
            ))}
          </div>
        ) : (
          <div className="bg-gray-50 rounded-2xl p-8 text-center text-gray-400">
            No hay prospectos con score calculado disponibles.
          </div>
        )}
      </div>

      {/* ============================================ */}
      {/* SECCIÓN 2: RESUMEN DEL MERCADO               */}
      {/* ============================================ */}
      <div>
        <h3 className="text-lg font-bold text-gray-800 mb-5 border-b pb-2">Resumen del Mercado</h3>

        {/* KPI Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {[
            { label: 'Total Restaurantes', value: stats?.total_restaurants ?? 0, color: 'text-primary-600', bg: 'bg-primary-50', icon: '🍽️' },
            { label: 'Rating Promedio', value: stats?.avg_rating ? `${stats.avg_rating.toFixed(1)} ★` : 'N/A', color: 'text-yellow-600', bg: 'bg-yellow-50', icon: '⭐' },
            { label: 'Alta Afinidad (≥70)', value: stats?.high_affinity_count ?? 0, color: 'text-green-600', bg: 'bg-green-50', icon: '🎯' },
            { label: 'Clientes Actuales', value: stats?.clients_count ?? 0, color: 'text-purple-600', bg: 'bg-purple-50', icon: '✅' },
          ].map((c) => (
            <div key={c.label} className={`${c.bg} rounded-2xl p-4 shadow-sm`}>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">{c.icon}</span>
                <p className="text-xs text-gray-500 font-medium">{c.label}</p>
              </div>
              <p className={`text-2xl font-bold ${c.color}`}>{c.value}</p>
            </div>
          ))}
        </div>

        {/* Charts 2x2 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Zona - horizontal bar */}
          <div className="bg-white rounded-2xl p-5 shadow-sm">
            <h4 className="text-sm font-semibold text-gray-700 mb-4">Restaurantes por Zona</h4>
            {zoneData && zoneData.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={[...zoneData].sort((a, b) => b.value - a.value).slice(0, 8)} layout="vertical">
                  <defs>
                    <linearGradient id="zoneGrad" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#9B1C2E" stopOpacity={1} />
                      <stop offset="100%" stopColor="#C94B6A" stopOpacity={0.7} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f5f5f5" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="label" width={110} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip cursor={{ fill: '#f9fafb' }} />
                  <Bar dataKey="value" fill="url(#zoneGrad)" radius={[0, 8, 8, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : <p className="text-gray-400 text-center py-8">Sin datos</p>}
          </div>

          {/* Fuente - donut */}
          <div className="bg-white rounded-2xl p-5 shadow-sm">
            <h4 className="text-sm font-semibold text-gray-700 mb-4">Distribución por Fuente</h4>
            {sourceChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={sourceChartData}
                    dataKey="value"
                    nameKey="label"
                    cx="50%"
                    cy="50%"
                    innerRadius={65}
                    outerRadius={95}
                    paddingAngle={4}
                    label={({ label, percent }) => `${label} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {sourceChartData.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : <p className="text-gray-400 text-center py-8">Sin datos</p>}
          </div>

          {/* Rating - area chart */}
          <div className="bg-white rounded-2xl p-5 shadow-sm">
            <h4 className="text-sm font-semibold text-gray-700 mb-4">Distribución por Rating</h4>
            {ratingData && ratingData.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={ratingData}>
                  <defs>
                    <linearGradient id="ratingGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#eab308" stopOpacity={0.5} />
                      <stop offset="95%" stopColor="#eab308" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f5f5f5" />
                  <XAxis dataKey="label" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
                  <Tooltip />
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke="#eab308"
                    strokeWidth={2.5}
                    fill="url(#ratingGrad)"
                    dot={{ r: 5, fill: '#eab308', strokeWidth: 2, stroke: 'white' }}
                    activeDot={{ r: 7 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : <p className="text-gray-400 text-center py-8">Sin datos</p>}
          </div>

          {/* Cocina - vertical bar con gradiente */}
          <div className="bg-white rounded-2xl p-5 shadow-sm">
            <h4 className="text-sm font-semibold text-gray-700 mb-4">Top 10 Tipos de Cocina</h4>
            {top10Cuisine.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={top10Cuisine}>
                  <defs>
                    <linearGradient id="cuisineGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#16a34a" stopOpacity={0.9} />
                      <stop offset="100%" stopColor="#4ade80" stopOpacity={0.6} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f5f5f5" vertical={false} />
                  <XAxis dataKey="label" tick={{ fontSize: 10 }} angle={-40} textAnchor="end" height={70} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip cursor={{ fill: '#f9fafb' }} />
                  <Bar dataKey="value" fill="url(#cuisineGrad)" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : <p className="text-gray-400 text-center py-8">Sin datos</p>}
          </div>
        </div>
      </div>

      {/* ============================================ */}
      {/* SECCIÓN 3: EMBUDO DE VENTAS                  */}
      {/* ============================================ */}
      <div>
        <h3 className="text-lg font-bold text-gray-800 mb-5 border-b pb-2">Embudo de Ventas</h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Funnel visual */}
          <div className="bg-white rounded-2xl p-5 shadow-sm">
            <h4 className="text-sm font-semibold text-gray-700 mb-4">Progresión de Estados</h4>
            <div className="space-y-3">
              {funnelData.map((stage, idx) => {
                const widthPct = maxFunnelCount > 0 ? (stage.count / maxFunnelCount) * 100 : 0;
                const colors = ['#9B1C2E', '#b91c1c', '#C94B6A', '#7F1D1D'];
                return (
                  <div key={stage.status}>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="font-medium text-gray-700">{stage.label}</span>
                      <span className="text-gray-500 font-semibold">{stage.count}</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-7 flex items-center">
                      <div
                        className="h-7 rounded-full transition-all flex items-center justify-center text-white text-xs font-bold"
                        style={{ width: `${Math.max(widthPct, 6)}%`, backgroundColor: colors[idx] }}
                      >
                        {widthPct >= 15 ? stage.count : ''}
                      </div>
                    </div>
                    {idx < funnelData.length - 1 && (
                      <div className="text-center text-gray-300 text-xs my-0.5">▼</div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Conversion table */}
          <div className="bg-white rounded-2xl p-5 shadow-sm">
            <h4 className="text-sm font-semibold text-gray-700 mb-4">Métricas de Conversión</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 rounded-lg">
                  <tr>
                    <th className="text-left py-3 px-4 font-medium text-gray-600 rounded-l-lg">Etapa</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Cantidad</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600 rounded-r-lg">Conv. anterior</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {funnelData.map((stage, idx) => (
                    <tr key={stage.status} className="hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium text-gray-700">{stage.label}</td>
                      <td className="py-3 px-4 text-right font-semibold">{stage.count}</td>
                      <td className="py-3 px-4 text-right">
                        {idx === 0 ? (
                          <span className="text-gray-300">—</span>
                        ) : (
                          <span className={`font-semibold ${stage.conversionRate >= 50 ? 'text-green-600' : 'text-orange-500'}`}>
                            {stage.conversionRate.toFixed(1)}%
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-4 bg-red-50 rounded-xl p-4 flex items-center justify-between">
              <div>
                <span className="text-sm font-semibold text-red-700">No Interesado</span>
                {stats && stats.total_restaurants > 0 && (
                  <p className="text-xs text-red-400 mt-0.5">
                    {((noInteresadoCount / stats.total_restaurants) * 100).toFixed(1)}% del total
                  </p>
                )}
              </div>
              <span className="text-2xl font-bold text-red-600">{noInteresadoCount}</span>
            </div>
          </div>
        </div>
      </div>

      {/* ============================================ */}
      {/* SECCIÓN 4: ANÁLISIS GEOGRÁFICO               */}
      {/* ============================================ */}
      <div>
        <h3 className="text-lg font-bold text-gray-800 mb-5 border-b pb-2">Análisis Geográfico</h3>

        {/* Map */}
        <div className="bg-white rounded-2xl p-5 shadow-sm mb-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-4">Mapa de Scores por Prospecto</h4>
          <div className="h-[400px] rounded-xl overflow-hidden">
            <MapContainer center={[-16.5, -68.15]} zoom={13} style={{ height: '100%', width: '100%' }}>
              <TileLayer
                attribution='&copy; OpenStreetMap'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {mapData?.map((point) => (
                <Marker key={point.id} position={[point.latitud, point.longitud]} icon={createScoreIcon(point.total_score)}>
                  <Popup>
                    <div className="text-sm">
                      <p className="font-semibold">{point.nombre}</p>
                      {point.rating && <p>Rating: {point.rating}/5</p>}
                      <p>Score: {point.total_score !== null ? point.total_score.toFixed(1) : 'Sin score'}</p>
                      <button onClick={() => navigate(`/restaurants/${point.id}`)} className="text-primary-500 hover:underline mt-1 block">
                        Ver detalle
                      </button>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
          <div className="flex gap-5 mt-3 text-xs text-gray-500">
            {[['#ef4444', 'Score < 50'], ['#eab308', 'Score 50–70'], ['#22c55e', 'Score 70+'], ['#9ca3af', 'Sin score']].map(([color, label]) => (
              <div key={label} className="flex items-center gap-1.5">
                <div style={{ background: color, width: 10, height: 10, borderRadius: '50%' }} />
                <span>{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Zone table */}
        <div className="bg-white rounded-2xl p-5 shadow-sm">
          <h4 className="text-sm font-semibold text-gray-700 mb-4">Detalle por Zona</h4>
          {zoneData && zoneData.length > 0 ? (
            <div className="overflow-x-auto max-h-[280px] overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <th className="text-left py-2.5 px-4 font-medium text-gray-600">Zona</th>
                    <th className="text-right py-2.5 px-4 font-medium text-gray-600">Restaurantes</th>
                    <th className="text-right py-2.5 px-4 font-medium text-gray-600">% del Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {[...zoneData].sort((a, b) => b.value - a.value).map((zone) => (
                    <tr key={zone.label} className="hover:bg-gray-50">
                      <td className="py-2.5 px-4 font-medium text-gray-700">{zone.label}</td>
                      <td className="py-2.5 px-4 text-right text-gray-600">{zone.value}</td>
                      <td className="py-2.5 px-4 text-right text-gray-400">
                        {stats ? ((zone.value / stats.total_restaurants) * 100).toFixed(1) : 0}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <p className="text-gray-400 text-center py-8">Sin datos</p>}
        </div>
      </div>
    </div>
  );
}
