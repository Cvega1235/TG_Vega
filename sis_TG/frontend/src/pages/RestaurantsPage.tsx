import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { getRestaurants, updateRestaurantStatus } from '../api/restaurants';
import { runScraper } from '../api/scraping';
import type { RestaurantFilters } from '../types/restaurant';
import StatusBadge from '../components/common/StatusBadge';
import ExportMenu from '../components/common/ExportMenu';
import { useAuth } from '../auth/AuthContext';
import { ZONAS_LA_PAZ, ALL_STATUSES, STATUS_LABELS } from '../utils/constants';

export default function RestaurantsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { hasRole } = useAuth();
  const [scrapingSource, setScrapingSource] = useState<'all' | 'bolivia' | 'gmaps'>('all');
  const [filters, setFilters] = useState<RestaurantFilters>({
    page: 1,
    per_page: 20,
    sort_by: 'id',
    sort_order: 'asc',
  });

  const scrapeMutation = useMutation({
    mutationFn: () => runScraper(scrapingSource, true),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurants'] });
    },
  });

  const { data, isLoading } = useQuery({
    queryKey: ['restaurants', filters],
    queryFn: () => getRestaurants(filters),
  });

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      updateRestaurantStatus(id, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['restaurants'] }),
  });

  const updateFilter = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value || undefined, page: 1 }));
  };

  const exportFilters: Record<string, string> = {};
  if (filters.fuente) exportFilters.fuente = filters.fuente;
  if (filters.zona) exportFilters.zona = filters.zona;
  if (filters.status) exportFilters.status = filters.status;
  if (filters.search) exportFilters.search = filters.search;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-800">Restaurantes</h2>
        <div className="flex items-center gap-3">
          {hasRole('admin') && (
            <>
              <select
                value={scrapingSource}
                onChange={(e) => setScrapingSource(e.target.value as 'all' | 'bolivia' | 'gmaps')}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
                disabled={scrapeMutation.isPending}
              >
                <option value="all">Todas las fuentes</option>
                <option value="bolivia">Bolivia en tus Manos</option>
                <option value="gmaps">Google Maps</option>
              </select>
              <button
                onClick={() => scrapeMutation.mutate()}
                disabled={scrapeMutation.isPending}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                {scrapeMutation.isPending ? 'Scrapeando...' : 'Ejecutar Scraping'}
              </button>
            </>
          )}
          <ExportMenu filters={exportFilters} />
        </div>
      </div>

      {scrapeMutation.isSuccess && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-green-800 font-medium">{scrapeMutation.data.message}</p>
          <p className="text-green-600 text-sm mt-1">
            Extraidos: {scrapeMutation.data.total_extracted} | Importados: {scrapeMutation.data.imported} | Duplicados: {scrapeMutation.data.duplicates}
          </p>
        </div>
      )}
      {scrapeMutation.isError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error al ejecutar el scraping. Verifica que Chrome este instalado.</p>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-xl p-4 shadow-sm flex flex-wrap gap-3">
        <input
          type="text"
          placeholder="Buscar por nombre o direccion..."
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm flex-1 min-w-[200px] focus:ring-2 focus:ring-primary-500 outline-none"
          value={filters.search || ''}
          onChange={(e) => updateFilter('search', e.target.value)}
        />
        <select
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
          value={filters.zona || ''}
          onChange={(e) => updateFilter('zona', e.target.value)}
        >
          <option value="">Todas las zonas</option>
          {ZONAS_LA_PAZ.map((z) => (
            <option key={z} value={z}>{z}</option>
          ))}
        </select>
        <select
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
          value={filters.status || ''}
          onChange={(e) => updateFilter('status', e.target.value)}
        >
          <option value="">Todos los estados</option>
          {ALL_STATUSES.map((s) => (
            <option key={s} value={s}>{STATUS_LABELS[s]}</option>
          ))}
        </select>
        <select
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
          value={filters.fuente || ''}
          onChange={(e) => updateFilter('fuente', e.target.value)}
        >
          <option value="">Todas las fuentes</option>
          <option value="Google Maps">Google Maps</option>
          <option value="TripAdvisor">TripAdvisor</option>
          <option value="Bolivia en tus Manos">Bolivia en tus Manos</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-400">Cargando...</div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="text-left py-3 px-4 text-gray-500 font-medium">Nombre</th>
                    <th className="text-left py-3 px-4 text-gray-500 font-medium">Zona</th>
                    <th className="text-left py-3 px-4 text-gray-500 font-medium">Fuente</th>
                    <th className="text-left py-3 px-4 text-gray-500 font-medium">Rating</th>
                    <th className="text-left py-3 px-4 text-gray-500 font-medium">Resenas</th>
                    <th className="text-left py-3 px-4 text-gray-500 font-medium">Estado</th>
                    <th className="text-right py-3 px-4 text-gray-500 font-medium">Score</th>
                    <th className="text-left py-3 px-4 text-gray-500 font-medium">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.items.map((r) => (
                    <tr
                      key={r.id}
                      className="border-t border-gray-100 hover:bg-gray-50 cursor-pointer"
                      onClick={() => navigate(`/restaurants/${r.id}`)}
                    >
                      <td className="py-3 px-4 font-medium text-gray-800">{r.nombre}</td>
                      <td className="py-3 px-4 text-gray-600">{r.zona || '-'}</td>
                      <td className="py-3 px-4 text-gray-600">{r.fuente}</td>
                      <td className="py-3 px-4 text-gray-600">
                        {r.rating ? `${r.rating}/5` : '-'}
                      </td>
                      <td className="py-3 px-4 text-gray-600">{r.num_resenas || 0}</td>
                      <td className="py-3 px-4" onClick={(e) => e.stopPropagation()}>
                        <select
                          value={r.status}
                          onChange={(e) =>
                            statusMutation.mutate({ id: r.id, status: e.target.value })
                          }
                          className="text-xs border border-gray-200 rounded px-2 py-1"
                        >
                          {ALL_STATUSES.map((s) => (
                            <option key={s} value={s}>{STATUS_LABELS[s]}</option>
                          ))}
                        </select>
                      </td>
                      <td className="py-3 px-4 text-right">
                        {r.score ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-primary-100 text-primary-700">
                            {r.score.total_score.toFixed(1)}
                          </span>
                        ) : '-'}
                      </td>
                      <td className="py-3 px-4">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/restaurants/${r.id}`);
                          }}
                          className="text-primary-500 hover:underline text-xs"
                        >
                          Ver
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {data && data.pages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
                <span className="text-sm text-gray-500">
                  {data.total} restaurantes | Pagina {data.page} de {data.pages}
                </span>
                <div className="flex gap-2">
                  <button
                    disabled={data.page <= 1}
                    onClick={() => setFilters((f) => ({ ...f, page: (f.page || 1) - 1 }))}
                    className="px-3 py-1 text-sm border border-gray-300 rounded-lg disabled:opacity-50 hover:bg-gray-50"
                  >
                    Anterior
                  </button>
                  <button
                    disabled={data.page >= data.pages}
                    onClick={() => setFilters((f) => ({ ...f, page: (f.page || 1) + 1 }))}
                    className="px-3 py-1 text-sm border border-gray-300 rounded-lg disabled:opacity-50 hover:bg-gray-50"
                  >
                    Siguiente
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
