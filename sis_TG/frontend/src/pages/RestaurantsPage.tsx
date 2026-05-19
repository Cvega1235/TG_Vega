import { useState, useEffect, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { getRestaurants, updateRestaurantStatus } from '../api/restaurants';
import { runScraper, getScrapingStatus } from '../api/scraping';
import type { ScrapingJob } from '../api/scraping';
import { useMutation } from '@tanstack/react-query';
import type { RestaurantFilters } from '../types/restaurant';
import ExportMenu from '../components/common/ExportMenu';
import Portal from '../components/common/Portal';
import { useAuth } from '../auth/AuthContext';
import { ZONAS_LA_PAZ, ALL_STATUSES, STATUS_LABELS } from '../utils/constants';

// ---------------------------------------------------------------------------
// Modal de confirmación de scraping
// ---------------------------------------------------------------------------
function ScrapingConfirmModal({
  onConfirm,
  onCancel,
}: {
  onConfirm: (source: 'all' | 'bolivia' | 'gmaps') => void;
  onCancel: () => void;
}) {
  const [selected, setSelected] = useState<'all' | 'bolivia' | 'gmaps'>('all');

  const sourceLabel: Record<string, string> = {
    all: 'Todas las fuentes (Google Maps + Bolivia en tus Manos + TripAdvisor + Sitios web)',
    gmaps: 'Google Maps + Sitios web propios',
    bolivia: 'Bolivia en tus Manos',
  };
  const estimatedTime: Record<string, string> = {
    all: '5 a 6 horas',
    gmaps: '3 a 4 horas',
    bolivia: '10 a 15 minutos',
  };

  return (
    <Portal>
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-xl p-6 max-w-md w-full mx-4">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-yellow-100 flex items-center justify-center text-yellow-600 text-xl font-bold flex-shrink-0">
            !
          </div>
          <h3 className="text-lg font-bold text-gray-800">Confirmar Scraping</h3>
        </div>

        <p className="text-gray-600 mb-4">
          Selecciona la fuente de datos a extraer e inicia el proceso.
        </p>

        {/* Selector de fuente */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Fuente de datos
          </label>
          <div className="space-y-2">
            {(['all', 'gmaps', 'bolivia'] as const).map((src) => (
              <label
                key={src}
                className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                  selected === src
                    ? 'border-green-500 bg-green-50'
                    : 'border-gray-200 hover:bg-gray-50'
                }`}
              >
                <input
                  type="radio"
                  name="source"
                  value={src}
                  checked={selected === src}
                  onChange={() => setSelected(src)}
                  className="mt-0.5 accent-green-600"
                />
                <div>
                  <p className="text-sm font-medium text-gray-800">
                    {src === 'all' ? 'Todas las fuentes' : src === 'gmaps' ? 'Google Maps' : 'Bolivia en tus Manos'}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">{sourceLabel[src]}</p>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Tiempo estimado */}
        <div className="bg-gray-50 rounded-lg px-4 py-3 mb-4 flex items-center justify-between text-sm">
          <span className="text-gray-600">Tiempo estimado:</span>
          <span className="text-orange-600 font-semibold">{estimatedTime[selected]}</span>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-5 text-sm text-yellow-800">
          El scraping se ejecutara en segundo plano. Puedes seguir usando la
          aplicacion mientras progresa, pero no cierres el servidor.
        </div>

        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancelar
          </button>
          <button
            onClick={() => onConfirm(selected)}
            className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
          >
            Iniciar Scraping
          </button>
        </div>
      </div>
    </div>
    </Portal>
  );
}

// ---------------------------------------------------------------------------
// Panel de progreso del scraping
// ---------------------------------------------------------------------------
function ScrapingProgressPanel({ job }: { job: ScrapingJob }) {
  const pct = job.steps_total > 0
    ? Math.round((job.steps_done / job.steps_total) * 100)
    : 0;

  const statusColor = {
    running: 'bg-blue-50 border-blue-200',
    completed: 'bg-green-50 border-green-200',
    error: 'bg-red-50 border-red-200',
  }[job.status];

  const barColor = {
    running: 'bg-blue-500',
    completed: 'bg-green-500',
    error: 'bg-red-500',
  }[job.status];

  const statusLabel = {
    running: 'En progreso...',
    completed: 'Completado',
    error: 'Error',
  }[job.status];

  return (
    <div className={`rounded-xl border p-4 ${statusColor}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {job.status === 'running' && (
            <div className="w-3 h-3 rounded-full bg-blue-500 animate-pulse" />
          )}
          <span className="font-medium text-gray-800 text-sm">
            Scraping — {statusLabel}
          </span>
        </div>
        <span className="text-sm font-bold text-gray-700">{pct}%</span>
      </div>

      {/* Barra de progreso */}
      <div className="w-full bg-gray-200 rounded-full h-3 mb-3">
        <div
          className={`h-3 rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* Paso actual */}
      <p className="text-xs text-gray-600 mb-2 truncate">
        {job.current_step || 'Iniciando...'}
      </p>

      {/* Estadísticas */}
      <div className="flex gap-4 text-xs text-gray-500">
        <span>Pasos: {job.steps_done}/{job.steps_total}</span>
        {job.total_scraped > 0 && (
          <span>Encontrados: {job.total_scraped}</span>
        )}
        {job.status === 'completed' && (
          <>
            <span className="text-green-700 font-medium">
              Importados: {job.imported}
            </span>
            <span>Omitidos: {job.skipped}</span>
          </>
        )}
      </div>

      {job.status === 'completed' && job.message && (
        <p className="mt-2 text-sm text-green-700 font-medium">{job.message}</p>
      )}
      {job.status === 'error' && job.message && (
        <p className="mt-2 text-sm text-red-700">{job.message}</p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Página principal
// ---------------------------------------------------------------------------
export default function RestaurantsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { hasRole } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const [scrapingSource, setScrapingSource] = useState<'all' | 'bolivia' | 'gmaps'>('all');
  const [showConfirm, setShowConfirm] = useState(false);
  const [activeJob, setActiveJob] = useState<ScrapingJob | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [filters, setFilters] = useState<RestaurantFilters>(() => {
    const initial: RestaurantFilters = {
      page: 1,
      per_page: 20,
      sort_by: searchParams.get('sort_by') || 'nombre',
      sort_order: searchParams.get('sort_order') || 'asc',
    };
    if (searchParams.get('status')) initial.status = searchParams.get('status')!;
    if (searchParams.get('min_score')) initial.min_score = parseFloat(searchParams.get('min_score')!);
    if (searchParams.get('tiene_embutidos') === 'true') initial.tiene_embutidos = true;
    if (searchParams.get('prospecto') === 'true') initial.prospecto = true;
    return initial;
  });

  // Polling: consulta el estado del job cada 5 segundos mientras esté activo
  useEffect(() => {
    if (!activeJob || activeJob.status !== 'running') {
      if (pollingRef.current) clearInterval(pollingRef.current);
      return;
    }
    pollingRef.current = setInterval(async () => {
      try {
        const updated = await getScrapingStatus(activeJob.job_id);
        setActiveJob(updated);
        if (updated.status === 'completed') {
          queryClient.invalidateQueries({ queryKey: ['restaurants'] });
        }
      } catch {
        // ignorar errores de red transitorios
      }
    }, 30000);

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [activeJob, queryClient]);

  const startMutation = useMutation({
    mutationFn: () => runScraper(scrapingSource, true),
    onSuccess: (data) => {
      // Crear estado inicial del job mientras llega el primer polling
      setActiveJob({
        job_id: data.job_id,
        status: 'running',
        source: scrapingSource,
        steps_done: 0,
        steps_total: scrapingSource === 'bolivia' ? 7 : scrapingSource === 'gmaps' ? 14 : 20,
        current_step: 'Iniciando...',
        total_scraped: 0,
        imported: 0,
        skipped: 0,
        message: '',
        started_at: new Date().toISOString(),
        finished_at: null,
      });
    },
  });

  const handleConfirm = (source: 'all' | 'bolivia' | 'gmaps') => {
    setScrapingSource(source);
    setShowConfirm(false);
    startMutation.mutate();
  };

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

  const updateBoolFilter = (key: string, value: string) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value === 'true' ? true : value === 'false' ? false : undefined,
      page: 1,
    }));
  };

  const updateNumFilter = (key: string, value: string) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value ? parseFloat(value) : undefined,
      page: 1,
    }));
  };

  const hasActiveFilters =
    !!(filters.search || filters.zona || filters.status || filters.fuente ||
       filters.tipo_cocina || filters.rating_min != null ||
       filters.tiene_embutidos != null || filters.min_score != null || filters.prospecto);

  const clearAllFilters = () => {
    setSearchParams({});
    setFilters({ page: 1, per_page: 20, sort_by: 'nombre', sort_order: 'asc' });
  };

  const exportFilters: Record<string, string> = {};
  if (filters.fuente) exportFilters.fuente = filters.fuente;
  if (filters.zona) exportFilters.zona = filters.zona;
  if (filters.status) exportFilters.status = filters.status;
  if (filters.search) exportFilters.search = filters.search;

  const activeDashboardFilter =
    filters.min_score != null ? `Score ≥ ${filters.min_score}`
    : filters.prospecto ? 'Prospectos a contactar'
    : filters.tiene_embutidos ? 'Con embutidos en menú'
    : filters.status === 'cliente' && !filters.zona ? 'Clientes actuales'
    : null;

  const clearDashboardFilter = () => {
    setSearchParams({});
    setFilters({ page: 1, per_page: 20, sort_by: 'nombre', sort_order: 'asc' });
  };

  const isScrapingRunning = activeJob?.status === 'running';

  return (
    <div className="space-y-6">
      {/* Modal de confirmación */}
      {showConfirm && (
        <ScrapingConfirmModal
          onConfirm={handleConfirm}
          onCancel={() => setShowConfirm(false)}
        />
      )}

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-800">Restaurantes</h2>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
          {hasRole('admin') && (
            <button
              onClick={() => setShowConfirm(true)}
              disabled={isScrapingRunning}
              className="w-full sm:w-auto bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm text-center"
            >
              {isScrapingRunning ? 'Scraping en curso...' : 'Ejecutar Scraping'}
            </button>
          )}
          <ExportMenu filters={exportFilters} />
        </div>
      </div>

      {/* Panel de progreso (visible mientras hay un job activo o recién completado) */}
      {activeJob && <ScrapingProgressPanel job={activeJob} />}

      {startMutation.isError && !activeJob && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error al iniciar el scraping. Verifica que Chrome este instalado.</p>
        </div>
      )}

      {/* Banner filtro desde dashboard */}
      {activeDashboardFilter && (
        <div className="bg-primary-50 border border-primary-200 rounded-xl px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-primary-700">
            <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2a1 1 0 01-.293.707L13 13.414V19a1 1 0 01-.553.894l-4 2A1 1 0 017 21v-7.586L3.293 6.707A1 1 0 013 6V4z" />
            </svg>
            <span>Filtro activo: <strong>{activeDashboardFilter}</strong></span>
          </div>
          <button
            onClick={clearDashboardFilter}
            className="text-xs text-primary-600 hover:text-primary-800 hover:underline ml-4 flex-shrink-0"
          >
            Quitar filtro
          </button>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-xl p-4 shadow-sm space-y-3">
        {/* Fila 1: búsqueda + tipo cocina */}
        <div className="flex flex-wrap gap-3">
          <input
            type="text"
            placeholder="Buscar por nombre o direccion..."
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm flex-1 min-w-[200px] focus:ring-2 focus:ring-primary-500 outline-none"
            value={filters.search || ''}
            onChange={(e) => updateFilter('search', e.target.value)}
          />
          <input
            type="text"
            placeholder="Tipo de cocina..."
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm w-44 focus:ring-2 focus:ring-primary-500 outline-none"
            value={filters.tipo_cocina || ''}
            onChange={(e) => updateFilter('tipo_cocina', e.target.value)}
          />
        </div>
        {/* Fila 2: selects */}
        <div className="flex flex-wrap gap-3">
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
          <select
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
            value={filters.rating_min != null ? String(filters.rating_min) : ''}
            onChange={(e) => updateNumFilter('rating_min', e.target.value)}
          >
            <option value="">Cualquier rating</option>
            <option value="4.5">Rating ≥ 4.5</option>
            <option value="4">Rating ≥ 4.0</option>
            <option value="3">Rating ≥ 3.0</option>
            <option value="2">Rating ≥ 2.0</option>
          </select>
          <select
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
            value={filters.tiene_embutidos == null ? '' : String(filters.tiene_embutidos)}
            onChange={(e) => updateBoolFilter('tiene_embutidos', e.target.value)}
          >
            <option value="">Embutidos: todos</option>
            <option value="true">Con embutidos</option>
            <option value="false">Sin embutidos</option>
          </select>
          <select
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
            value={filters.min_score != null ? String(filters.min_score) : ''}
            onChange={(e) => updateNumFilter('min_score', e.target.value)}
          >
            <option value="">Cualquier score</option>
            <option value="90">Score ≥ 90</option>
            <option value="80">Score ≥ 80</option>
            <option value="70">Score ≥ 70 (Alta afinidad)</option>
            <option value="50">Score ≥ 50</option>
          </select>
          {hasActiveFilters && (
            <button
              onClick={clearAllFilters}
              className="px-3 py-2 text-sm text-red-500 border border-red-200 rounded-lg hover:bg-red-50 transition-colors"
            >
              Limpiar filtros
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm">
        {isLoading ? (
          <div className="p-8 text-center text-gray-400">Cargando...</div>
        ) : (
          <>
            <div className="rounded-t-xl">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="text-left py-3 px-3 sm:px-4 text-gray-500 font-medium">Nombre</th>
                    <th className="text-left py-3 px-3 sm:px-4 text-gray-500 font-medium hidden sm:table-cell">Zona</th>
                    <th className="text-left py-3 px-3 sm:px-4 text-gray-500 font-medium hidden lg:table-cell">Fuente</th>
                    <th className="text-left py-3 px-3 sm:px-4 text-gray-500 font-medium hidden md:table-cell">Rating</th>
                    <th className="text-left py-3 px-3 sm:px-4 text-gray-500 font-medium hidden xl:table-cell">Reseñas</th>
                    <th className="text-left py-3 px-3 sm:px-4 text-gray-500 font-medium">Estado</th>
                    <th className="text-right py-3 px-3 sm:px-4 text-gray-500 font-medium hidden sm:table-cell">Score</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.items.map((r) => (
                    <tr
                      key={r.id}
                      className="border-t border-gray-100 hover:bg-gray-50 cursor-pointer"
                      onClick={() => navigate(`/restaurants/${r.id}`)}
                    >
                      <td className="py-2.5 px-3 sm:px-4 font-medium text-gray-800">
                        <span className="block max-w-[160px] sm:max-w-xs truncate">{r.nombre}</span>
                        <span className="text-xs text-gray-400 sm:hidden">{r.zona || ''}</span>
                      </td>
                      <td className="py-2.5 px-3 sm:px-4 text-gray-600 hidden sm:table-cell">{r.zona || '-'}</td>
                      <td className="py-2.5 px-3 sm:px-4 text-gray-600 hidden lg:table-cell">{r.fuente}</td>
                      <td className="py-2.5 px-3 sm:px-4 text-gray-600 hidden md:table-cell">
                        {r.rating ? `${r.rating}/5` : '-'}
                      </td>
                      <td className="py-2.5 px-3 sm:px-4 text-gray-600 hidden xl:table-cell">{r.num_resenas || 0}</td>
                      <td className="py-2.5 px-3 sm:px-4" onClick={(e) => e.stopPropagation()}>
                        <select
                          value={r.status}
                          onChange={(e) => statusMutation.mutate({ id: r.id, status: e.target.value })}
                          className="text-xs border border-gray-200 rounded px-1.5 py-1 w-full max-w-[120px]"
                        >
                          {ALL_STATUSES.map((s) => (
                            <option key={s} value={s}>{STATUS_LABELS[s]}</option>
                          ))}
                        </select>
                      </td>
                      <td className="py-2.5 px-3 sm:px-4 text-right hidden sm:table-cell">
                        {r.score ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-primary-100 text-primary-700">
                            {r.score.total_score.toFixed(1)}
                          </span>
                        ) : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {data && data.pages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 rounded-b-xl">
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
