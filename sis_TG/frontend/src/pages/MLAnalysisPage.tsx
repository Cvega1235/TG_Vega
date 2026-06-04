import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell, ResponsiveContainer,
} from 'recharts';
import {
  getLatestRun, getClusterProfiles, getTopProspects, runMLPipeline,
  getScoringWeights, updateScoringWeights,
} from '../api/ml';
import type { ScoringWeights } from '../api/ml';
import { useAuth } from '../auth/AuthContext';
import Portal from '../components/common/Portal';

const CLUSTER_NAMES: Record<number, { label: string; desc: string; color: string }> = {
  0: {
    label: 'Alta Visibilidad Internacional',
    desc: 'Establecimientos con gran presencia en plataformas internacionales, muchas reseñas y alto perfil turístico.',
    color: '#2196F3',
  },
  1: {
    label: 'Mercado Local',
    desc: 'Restaurantes y cafeterías del mercado local de La Paz. Segmento principal de clientes de Don Piotr.',
    color: '#4CAF50',
  },
};

function ScoreBar({ value, max = 100 }: { value: number; max?: number }) {
  const pct = Math.min((value / max) * 100, 100);
  const color = value >= 70 ? '#4CAF50' : value >= 50 ? '#FF9800' : '#F44336';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-200 rounded-full h-2.5">
        <div className="h-2.5 rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <span className="text-xs font-bold w-7 text-right shrink-0" style={{ color }}>{value.toFixed(0)}</span>
    </div>
  );
}

function ClusterCard({ clusterId, size, avgRating, dominantZone, dominantCuisine }: {
  clusterId: number; size: number; avgRating: number | null;
  dominantZone: string | null; dominantCuisine: string | null;
}) {
  const info = CLUSTER_NAMES[clusterId] ?? { label: `Segmento ${clusterId}`, desc: '', color: '#9E9E9E' };
  return (
    <div className="bg-white rounded-xl shadow p-4 sm:p-5 border-t-4" style={{ borderColor: info.color }}>
      <div className="flex items-start justify-between mb-3">
        <div className="min-w-0 mr-2">
          <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: info.color }}>
            Segmento {clusterId}
          </span>
          <h3 className="text-base sm:text-lg font-bold text-gray-800 mt-0.5 leading-tight">{info.label}</h3>
        </div>
        <span className="text-2xl sm:text-3xl font-black shrink-0" style={{ color: info.color }}>{size}</span>
      </div>
      <p className="text-sm text-gray-500 mb-4">{info.desc}</p>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 sm:gap-3 text-center text-sm">
        <div className="bg-gray-50 rounded-lg p-2">
          <p className="text-gray-400 text-xs">Rating prom.</p>
          <p className="font-bold text-gray-700">{avgRating?.toFixed(1) ?? '—'}</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-2">
          <p className="text-gray-400 text-xs">Zona principal</p>
          <p className="font-bold text-gray-700 truncate">{dominantZone ?? '—'}</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-2 col-span-2 sm:col-span-1">
          <p className="text-gray-400 text-xs">Cocina principal</p>
          <p className="font-bold text-gray-700 truncate">{dominantCuisine ?? '—'}</p>
        </div>
      </div>
    </div>
  );
}

const WEIGHT_LABELS: Record<keyof ScoringWeights, { label: string; max: number; color: string }> = {
  w_cuisine: { label: 'Afinidad Cocina', max: 30, color: 'bg-blue-500' },
  w_rating: { label: 'Rating', max: 20, color: 'bg-yellow-500' },
  w_reviews: { label: 'Volumen Reseñas', max: 15, color: 'bg-green-500' },
  w_zone: { label: 'Afinidad de Zona', max: 15, color: 'bg-purple-500' },
  w_price: { label: 'Nivel Precio', max: 10, color: 'bg-orange-500' },
  w_completeness: { label: 'Completitud Datos', max: 10, color: 'bg-red-500' },
};

const DEFAULT_WEIGHTS: ScoringWeights = {
  w_cuisine: 30, w_rating: 20, w_reviews: 15,
  w_zone: 15, w_price: 10, w_completeness: 10,
};

function ScoringWeightsPanel() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [local, setLocal] = useState<ScoringWeights | null>(null);
  const [saved, setSaved] = useState(false);

  const { data: remote } = useQuery({
    queryKey: ['scoring-weights'],
    queryFn: getScoringWeights,
    staleTime: Infinity,
  });

  const weights = local ?? remote ?? DEFAULT_WEIGHTS;
  const total = Object.values(weights).reduce((a, b) => a + b, 0);
  const isValid = Math.abs(total - 100) < 0.1;

  const saveMutation = useMutation({
    mutationFn: updateScoringWeights,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scoring-weights'] });
      setLocal(null);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    },
  });

  function handleChange(key: keyof ScoringWeights, rawValue: number) {
    setSaved(false);
    const current = local ?? remote ?? DEFAULT_WEIGHTS;
    const otherTotal = (Object.keys(current) as (keyof ScoringWeights)[])
      .filter(k => k !== key)
      .reduce((sum, k) => sum + current[k], 0);
    // Cap so the total never exceeds 100; min 1
    const newValue = Math.min(Math.max(1, rawValue), 100 - otherTotal);
    setLocal({ ...current, [key]: newValue });
  }

  function handleReset() {
    setLocal({ ...DEFAULT_WEIGHTS });
    setSaved(false);
  }

  return (
    <div className="bg-white rounded-xl shadow overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-5 py-4 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
          </svg>
          <span className="text-sm font-semibold text-gray-700">Configuración de Pesos del Scoring</span>
        </div>
        <svg className={`w-4 h-4 text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="px-5 pb-5 border-t border-gray-100 pt-4 space-y-4">
          <p className="text-xs text-gray-500">
            Ajusta el peso máximo de cada variable. Los pesos deben sumar exactamente 100.
            Los cambios se aplican al ejecutar el análisis ML.
          </p>

          <div className="space-y-3">
            {(Object.keys(WEIGHT_LABELS) as (keyof ScoringWeights)[]).map((key) => {
              const meta = WEIGHT_LABELS[key];
              const val = weights[key];
              return (
                <div key={key} className="flex items-center gap-3">
                  <span className="text-xs text-gray-600 w-36 shrink-0">{meta.label}</span>
                  <input
                    type="range"
                    min={1}
                    max={95}
                    step={1}
                    value={val}
                    onChange={(e) => handleChange(key, Number(e.target.value))}
                    className="flex-1 accent-primary-600"
                  />
                  <input
                    type="number"
                    min={1}
                    max={95}
                    value={val}
                    onChange={(e) => handleChange(key, Number(e.target.value))}
                    className="w-14 text-center border border-gray-300 rounded-lg px-1 py-1 text-sm focus:ring-2 focus:ring-primary-400 outline-none"
                  />
                </div>
              );
            })}
          </div>

          <div className={`flex items-center gap-2 text-sm font-medium px-3 py-2 rounded-lg ${isValid ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-700'
            }`}>
            <span>Total:</span>
            <span className="font-bold">{total} / 100</span>
            {!isValid && (
              <span className="text-xs ml-1">
                — faltan <strong>{100 - total}</strong> pts por asignar
              </span>
            )}
          </div>

          {saved && (
            <p className="text-xs text-green-600 font-medium">
              Pesos guardados correctamente. Ejecuta el análisis ML para aplicarlos.
            </p>
          )}
          {saveMutation.isError && (
            <p className="text-xs text-red-600">Error al guardar. Intenta nuevamente.</p>
          )}

          <div className="flex gap-3 justify-end pt-1">
            <button
              onClick={handleReset}
              className="px-4 py-1.5 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Restablecer
            </button>
            <button
              onClick={() => saveMutation.mutate(weights)}
              disabled={!isValid || saveMutation.isPending}
              className="px-4 py-1.5 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {saveMutation.isPending ? 'Guardando...' : 'Guardar pesos'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function MLConfirmModal({ onConfirm, onCancel }: { onConfirm: () => void; onCancel: () => void }) {
  return (
    <Portal>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
        <div className="bg-white rounded-xl shadow-xl p-5 sm:p-6 w-full max-w-md">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-xl font-bold shrink-0">
              ?
            </div>
            <h3 className="text-lg font-bold text-gray-800">Confirmar Analisis ML</h3>
          </div>
          <p className="text-gray-600 mb-4 text-sm sm:text-base">
            Estas a punto de ejecutar el pipeline de Machine Learning sobre todos los restaurantes.
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4 space-y-2 text-sm text-blue-800">
            <p className="font-medium">Esta operacion realizara lo siguiente:</p>
            <ul className="list-disc list-inside space-y-1 text-blue-700">
              <li>Recalcular los clusters de segmentacion (K-Means)</li>
              <li>Recalcular el Perfil de Cliente Ideal (ICP)</li>
              <li>Recalcular el score de afinidad de todos los restaurantes</li>
              <li>Sobreescribir los puntajes ML anteriores</li>
            </ul>
          </div>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-5 text-sm text-yellow-800">
            El analisis puede tardar varios minutos dependiendo del numero de restaurantes en la base de datos.
          </div>
          <div className="flex gap-3 justify-end">
            <button
              onClick={onCancel}
              className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              onClick={onConfirm}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
            >
              Ejecutar Analisis
            </button>
          </div>
        </div>
      </div>
    </Portal>
  );
}

export default function MLAnalysisPage() {
  const { hasRole } = useAuth();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [prospectLimit, setProspectLimit] = useState(20);
  const [includeClients, setIncludeClients] = useState(false);
  const [showMLConfirm, setShowMLConfirm] = useState(false);

  const { data: latestRun } = useQuery({ queryKey: ['ml-latest-run'], queryFn: getLatestRun });
  const { data: clusters, isLoading: loadingClusters } = useQuery({ queryKey: ['ml-clusters'], queryFn: getClusterProfiles });
  const { data: prospects, isLoading: loadingProspects } = useQuery({
    queryKey: ['ml-top-prospects', prospectLimit, includeClients],
    queryFn: () => getTopProspects(prospectLimit, includeClients),
  });

  const runPipeline = useMutation({
    mutationFn: runMLPipeline,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ml-latest-run'] });
      queryClient.invalidateQueries({ queryKey: ['ml-clusters'] });
      queryClient.invalidateQueries({ queryKey: ['ml-top-prospects'] });
    },
  });

  const isLoading = loadingClusters || loadingProspects;

  return (
    <div className="space-y-5 sm:space-y-6">
      {showMLConfirm && (
        <MLConfirmModal
          onConfirm={() => { setShowMLConfirm(false); runPipeline.mutate(); }}
          onCancel={() => setShowMLConfirm(false)}
        />
      )}

      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Analisis de Prospectos</h1>
          <p className="text-gray-500 mt-1 text-sm sm:text-base">
            Clasificacion automatica de clientes potenciales para Don Piotr
          </p>
        </div>
        {hasRole('admin') && (
          <button
            onClick={() => setShowMLConfirm(true)}
            disabled={runPipeline.isPending}
            className="w-full sm:w-auto bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2 text-sm"
          >
            <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {runPipeline.isPending ? 'Analizando...' : 'Actualizar Analisis'}
          </button>
        )}
      </div>

      {runPipeline.isSuccess && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-green-800 font-medium text-sm sm:text-base">{runPipeline.data.message}</p>
        </div>
      )}
      {runPipeline.isError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 text-sm">Error al actualizar el analisis.</p>
        </div>
      )}

      {!latestRun && !isLoading && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <p className="text-yellow-800 text-base font-medium">Analisis no ejecutado aun</p>
          <p className="text-yellow-600 mt-1 text-sm">Presiona "Actualizar Analisis" para clasificar los prospectos.</p>
        </div>
      )}

      {/* Resumen del modelo */}
      {latestRun && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 sm:p-5">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 sm:w-6 sm:h-6 text-blue-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p className="font-semibold text-blue-800 text-sm sm:text-base">Como funciona el analisis</p>
              <p className="text-xs sm:text-sm text-blue-700 mt-1">
                El sistema analizo <strong>{latestRun.total_restaurants_scored} restaurantes</strong> de La Paz
                y los clasifico en <strong>{latestRun.optimal_k} segmentos</strong> segun sus caracteristicas
                (zona, tipo de cocina, rating, reseñas). Luego comparo cada restaurante con el perfil de los{' '}
                <strong>{latestRun.icp_clients_count} clientes actuales</strong> de Don Piotr para asignar
                un score de afinidad del 0 al 100.
              </p>
              <p className="text-xs text-blue-500 mt-2">
                Ultimo analisis: {new Date(latestRun.run_at).toLocaleString('es-BO')}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Configuración de pesos — solo admin */}
      {hasRole('admin') && <ScoringWeightsPanel />}

      {/* Tarjetas de segmentos */}
      {clusters && clusters.length > 0 && (
        <>
          <h2 className="text-base sm:text-lg font-semibold text-gray-800">Segmentos de Mercado Identificados</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
            {clusters.map((c) => (
              <ClusterCard
                key={c.cluster_id}
                clusterId={c.cluster_id}
                size={c.size}
                avgRating={c.avg_rating}
                dominantZone={c.dominant_zone}
                dominantCuisine={c.dominant_cuisine}
              />
            ))}
          </div>
        </>
      )}

      {/* Graficos */}
      {clusters && clusters.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
          <div className="bg-white rounded-xl shadow p-4 sm:p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Distribucion de Restaurantes por Segmento</h3>
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie
                  data={clusters.map(c => ({
                    name: CLUSTER_NAMES[c.cluster_id]?.label ?? `Segmento ${c.cluster_id}`,
                    value: c.size,
                  }))}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={85}
                  label={({ percent }) => `${(percent * 100).toFixed(0)}%`}
                >
                  {clusters.map((c) => (
                    <Cell key={c.cluster_id} fill={CLUSTER_NAMES[c.cluster_id]?.color ?? '#9E9E9E'} />
                  ))}
                </Pie>
                <Tooltip formatter={(value, name) => [value, name]} />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-xl shadow p-4 sm:p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Score de Afinidad Promedio por Segmento</h3>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart
                data={clusters.map(c => ({
                  name: CLUSTER_NAMES[c.cluster_id]?.label ?? `Segmento ${c.cluster_id}`,
                  score: c.avg_composite_score ? Math.round(c.avg_composite_score) : 0,
                  rating: c.avg_rating ?? 0,
                }))}
                margin={{ left: -10 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Bar dataKey="score" fill="#2196F3" name="Score Afinidad" radius={[4, 4, 0, 0]} />
                <Bar dataKey="rating" fill="#4CAF50" name="Rating Prom." radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Top prospectos */}
      {prospects && prospects.length > 0 && (
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <div className="px-4 sm:px-6 py-4 border-b flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-semibold text-gray-800">Mejores Prospectos</h2>
              <p className="text-xs text-gray-400 mt-0.5">Restaurantes con mayor afinidad al perfil de cliente Don Piotr</p>
            </div>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
              <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={includeClients}
                  onChange={e => setIncludeClients(e.target.checked)}
                  className="w-4 h-4 accent-primary-600 cursor-pointer"
                />
                Incluir clientes actuales
              </label>
              <select
                value={prospectLimit}
                onChange={e => setProspectLimit(Number(e.target.value))}
                className="border rounded px-3 py-1.5 text-sm w-full sm:w-auto"
              >
                <option value={10}>Top 10</option>
                <option value={20}>Top 20</option>
                <option value={50}>Top 50</option>
              </select>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 sm:px-4 py-3 text-left font-medium text-gray-500 w-8">#</th>
                  <th className="px-3 sm:px-4 py-3 text-left font-medium text-gray-500">Restaurante</th>
                  <th className="px-3 sm:px-4 py-3 text-left font-medium text-gray-500 hidden sm:table-cell">Zona</th>
                  <th className="px-3 sm:px-4 py-3 text-right font-medium text-gray-500 hidden md:table-cell">Rating</th>
                  <th className="px-3 sm:px-4 py-3 text-left font-medium text-gray-500 hidden lg:table-cell">Cocina</th>
                  <th className="px-3 sm:px-4 py-3 text-left font-medium text-gray-500 w-32 sm:w-40">Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {prospects.map((p, i) => (
                  <tr
                    key={p.id}
                    className="hover:bg-primary-50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/restaurants/${p.id}`)}
                  >
                    <td className="px-3 sm:px-4 py-2.5 sm:py-3 text-gray-400 font-mono text-xs">{i + 1}</td>
                    <td className="px-3 sm:px-4 py-2.5 sm:py-3 font-medium text-gray-800">
                      <span className="block max-w-[160px] sm:max-w-xs truncate text-primary-600 hover:underline">{p.nombre}</span>
                      <span className="text-xs text-gray-400 sm:hidden">{p.zona ?? ''}</span>
                    </td>
                    <td className="px-3 sm:px-4 py-2.5 sm:py-3 text-gray-500 hidden sm:table-cell">{p.zona ?? '—'}</td>
                    <td className="px-3 sm:px-4 py-2.5 sm:py-3 text-right hidden md:table-cell">
                      {p.rating ? (
                        <span className="flex items-center justify-end gap-1">
                          <svg className="w-3 h-3 text-yellow-400 fill-yellow-400" viewBox="0 0 24 24">
                            <path d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                          </svg>
                          {p.rating.toFixed(1)}
                        </span>
                      ) : '—'}
                    </td>
                    <td className="px-3 sm:px-4 py-2.5 sm:py-3 text-gray-500 hidden lg:table-cell">
                      <span className="block max-w-[140px] truncate">{p.tipo_cocina ?? '—'}</span>
                    </td>
                    <td className="px-3 sm:px-4 py-2.5 sm:py-3 w-32 sm:w-40">
                      <ScoreBar value={p.total_score ?? p.composite_score ?? 0} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      )}
    </div>
  );
}
