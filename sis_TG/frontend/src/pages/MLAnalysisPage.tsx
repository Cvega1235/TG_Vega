import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell, ResponsiveContainer,
} from 'recharts';
import { getLatestRun, getClusterProfiles, getTopProspects, runMLPipeline } from '../api/ml';
import { useAuth } from '../auth/AuthContext';
import type { ClusterProfile, TopProspect } from '../types/ml';

const COLORS = ['#2196F3', '#4CAF50', '#FF9800', '#F44336', '#9C27B0',
  '#00BCD4', '#795548', '#607D8B', '#E91E63', '#3F51B5'];

function ScoreBar({ value, max = 100, color = '#2196F3' }: { value: number; max?: number; color?: string }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="w-full bg-gray-200 rounded-full h-4">
      <div
        className="h-4 rounded-full transition-all"
        style={{ width: `${pct}%`, backgroundColor: color }}
      />
    </div>
  );
}

export default function MLAnalysisPage() {
  const { hasRole } = useAuth();
  const queryClient = useQueryClient();
  const [prospectLimit, setProspectLimit] = useState(20);

  const { data: latestRun, isLoading: loadingRun } = useQuery({
    queryKey: ['ml-latest-run'],
    queryFn: getLatestRun,
  });

  const { data: clusters, isLoading: loadingClusters } = useQuery({
    queryKey: ['ml-clusters'],
    queryFn: getClusterProfiles,
  });

  const { data: prospects, isLoading: loadingProspects } = useQuery({
    queryKey: ['ml-top-prospects', prospectLimit],
    queryFn: () => getTopProspects(prospectLimit),
  });

  const runPipeline = useMutation({
    mutationFn: runMLPipeline,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ml-latest-run'] });
      queryClient.invalidateQueries({ queryKey: ['ml-clusters'] });
      queryClient.invalidateQueries({ queryKey: ['ml-top-prospects'] });
    },
  });

  const isLoading = loadingRun || loadingClusters || loadingProspects;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analisis ML</h1>
          <p className="text-gray-500 mt-1">
            Clustering K-means y scoring de clientes potenciales
          </p>
        </div>
        {hasRole('admin') && (
          <button
            onClick={() => runPipeline.mutate()}
            disabled={runPipeline.isPending}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {runPipeline.isPending ? 'Ejecutando...' : 'Ejecutar Pipeline ML'}
          </button>
        )}
      </div>

      {/* Pipeline Result Message */}
      {runPipeline.isSuccess && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-green-800 font-medium">{runPipeline.data.message}</p>
        </div>
      )}
      {runPipeline.isError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error al ejecutar el pipeline ML</p>
        </div>
      )}

      {/* Metrics Cards */}
      {latestRun && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Clusters (K)"
            value={latestRun.optimal_k}
          />
          <MetricCard
            title="Silhouette Score"
            value={latestRun.silhouette_score.toFixed(4)}
            status={latestRun.silhouette_score >= 0.5 ? 'good' : 'warning'}
          />
          <MetricCard
            title="Davies-Bouldin"
            value={latestRun.davies_bouldin_index.toFixed(4)}
          />
          <MetricCard
            title="Restaurantes Evaluados"
            value={latestRun.total_restaurants_scored}
          />
        </div>
      )}

      {!latestRun && !isLoading && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <p className="text-yellow-800 text-lg">
            No se ha ejecutado el pipeline ML aun.
          </p>
          <p className="text-yellow-600 mt-1">
            Presiona "Ejecutar Pipeline ML" para comenzar el analisis.
          </p>
        </div>
      )}

      {/* Cluster Distribution Charts */}
      {clusters && clusters.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Pie Chart - Cluster Distribution */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Distribucion de Clusters</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={clusters.map(c => ({ name: c.label || `Cluster ${c.cluster_id}`, value: c.size }))}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                >
                  {clusters.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Bar Chart - Avg Score by Cluster */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Score Promedio por Cluster</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={clusters.map(c => ({
                name: c.label || `Cluster ${c.cluster_id}`,
                score: c.avg_composite_score || 0,
                rating: c.avg_rating || 0,
              }))}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="score" fill="#2196F3" name="Score Compuesto" />
                <Bar dataKey="rating" fill="#4CAF50" name="Rating Promedio" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Cluster Profiles Table */}
      {clusters && clusters.length > 0 && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b">
            <h2 className="text-lg font-semibold">Perfiles de Clusters</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Cluster</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Tamano</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Rating Prom.</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Resenas Prom.</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Cocina</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Zona</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Precio</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {clusters.map((c, i) => (
                  <tr key={c.cluster_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <span
                        className="inline-block w-3 h-3 rounded-full mr-2"
                        style={{ backgroundColor: COLORS[i % COLORS.length] }}
                      />
                      {c.label || `Cluster ${c.cluster_id}`}
                    </td>
                    <td className="px-4 py-3 text-right">{c.size}</td>
                    <td className="px-4 py-3 text-right">{c.avg_rating?.toFixed(1) ?? '-'}</td>
                    <td className="px-4 py-3 text-right">{c.avg_reviews?.toFixed(0) ?? '-'}</td>
                    <td className="px-4 py-3">{c.dominant_cuisine ?? '-'}</td>
                    <td className="px-4 py-3">{c.dominant_zone ?? '-'}</td>
                    <td className="px-4 py-3">{c.dominant_price ?? '-'}</td>
                    <td className="px-4 py-3 text-right font-semibold">
                      {c.avg_composite_score?.toFixed(1) ?? '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Top Prospects */}
      {prospects && prospects.length > 0 && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b flex items-center justify-between">
            <h2 className="text-lg font-semibold">Top Prospectos</h2>
            <select
              value={prospectLimit}
              onChange={e => setProspectLimit(Number(e.target.value))}
              className="border rounded px-3 py-1 text-sm"
            >
              <option value={10}>Top 10</option>
              <option value={20}>Top 20</option>
              <option value={50}>Top 50</option>
            </select>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">#</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Restaurante</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Fuente</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Zona</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Rating</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Cocina</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Similitud ICP</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Score</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600 w-32">Barra</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {prospects.map((p, i) => (
                  <tr key={p.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-500">{i + 1}</td>
                    <td className="px-4 py-3 font-medium">{p.nombre}</td>
                    <td className="px-4 py-3 text-gray-500">{p.fuente}</td>
                    <td className="px-4 py-3">{p.zona ?? '-'}</td>
                    <td className="px-4 py-3 text-right">{p.rating?.toFixed(1) ?? '-'}</td>
                    <td className="px-4 py-3 text-gray-500">{p.tipo_cocina ?? '-'}</td>
                    <td className="px-4 py-3 text-right">{p.icp_similarity?.toFixed(1) ?? '-'}</td>
                    <td className="px-4 py-3 text-right font-bold">
                      {p.composite_score?.toFixed(1) ?? '-'}
                    </td>
                    <td className="px-4 py-3">
                      <ScoreBar
                        value={p.composite_score ?? 0}
                        color={
                          (p.composite_score ?? 0) >= 70 ? '#4CAF50'
                            : (p.composite_score ?? 0) >= 50 ? '#FF9800'
                              : '#F44336'
                        }
                      />
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

function MetricCard({
  title,
  value,
  status,
}: {
  title: string;
  value: string | number;
  status?: 'good' | 'warning' | 'bad';
}) {
  const statusColor = status === 'good' ? 'text-green-600'
    : status === 'warning' ? 'text-yellow-600'
      : status === 'bad' ? 'text-red-600'
        : 'text-gray-900';

  return (
    <div className="bg-white rounded-lg shadow p-5">
      <p className="text-sm text-gray-500">{title}</p>
      <p className={`text-2xl font-bold mt-1 ${statusColor}`}>{value}</p>
    </div>
  );
}
