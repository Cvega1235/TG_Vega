import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getScrapingHistory, runScraper, getScrapingStatus, getSchedule, saveSchedule, cancelSchedule } from '../api/scraping';
import type { ScrapingJob } from '../api/scraping';

function sourceLabel(source_file: string | null): string {
  if (!source_file) return 'Importación';
  if (source_file.includes('gmaps')) return 'Google Maps';
  if (source_file.includes('bolivia')) return 'Bolivia en tus Manos';
  if (source_file.includes('tripadvisor')) return 'TripAdvisor';
  if (source_file.includes('all')) return 'Todas las fuentes';
  return source_file;
}

function StatusPill({ status }: { status: ScrapingJob['status'] }) {
  const styles = {
    running: 'bg-blue-50 text-blue-700 border-blue-200',
    completed: 'bg-green-50 text-green-700 border-green-200',
    error: 'bg-red-50 text-red-600 border-red-200',
  };
  const labels = { running: 'En curso', completed: 'Completado', error: 'Error' };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${styles[status]}`}>
      {labels[status]}
    </span>
  );
}

const INTERVAL_OPTIONS = [
  { value: 15, label: 'Cada 15 días' },
  { value: 30, label: 'Cada mes' },
  { value: 60, label: 'Cada 2 meses' },
];

const SOURCE_OPTIONS = [
  { value: 'all',     label: 'Todas las fuentes' },
  { value: 'gmaps',   label: 'Google Maps' },
  { value: 'bolivia', label: 'Bolivia en tus Manos' },
];

function ScheduleSection() {
  const queryClient = useQueryClient();
  const { data: schedule, isLoading } = useQuery({
    queryKey: ['scrapingSchedule'],
    queryFn: getSchedule,
  });

  const defaultStart = () => {
    const d = new Date();
    d.setMinutes(0, 0, 0);
    d.setHours(d.getHours() + 1);
    return d.toISOString().slice(0, 16);
  };

  const [intervalDays, setIntervalDays] = useState(30);
  const [source, setSource] = useState('all');
  const [startAt, setStartAt] = useState(defaultStart);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (schedule?.active && schedule.interval_days) {
      setIntervalDays(schedule.interval_days);
      setSource(schedule.source ?? 'all');
      if (schedule.start_at) setStartAt(schedule.start_at.slice(0, 16));
    }
  }, [schedule]);

  const saveMutation = useMutation({
    mutationFn: () => saveSchedule(intervalDays, source, new Date(startAt).toISOString()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scrapingSchedule'] });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    },
  });

  const cancelMutation = useMutation({
    mutationFn: cancelSchedule,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['scrapingSchedule'] }),
  });

  if (isLoading) return null;

  const isActive = schedule?.active ?? false;
  const nextRun = schedule?.next_run_at
    ? new Date(schedule.next_run_at).toLocaleString('es-ES', {
        day: 'numeric', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
      })
    : null;

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gray-700">Scraping Programado</h3>
          <p className="text-xs text-gray-400 mt-0.5">Automatiza la recolección de datos periódicamente</p>
        </div>
        {isActive && (
          <span className="flex items-center gap-1.5 text-xs font-medium text-green-700 bg-green-50 border border-green-200 px-2.5 py-1 rounded-full">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
            Activo
          </span>
        )}
      </div>

      {isActive && nextRun && (
        <div className="flex items-center gap-2 bg-blue-50 border border-blue-100 rounded-lg px-4 py-2.5">
          <svg className="w-4 h-4 text-blue-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <span className="text-xs text-blue-700">Próxima ejecución: <strong>{nextRun}</strong></span>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label className="text-xs text-gray-500 font-medium block mb-1">Intervalo</label>
          <select
            value={intervalDays}
            onChange={(e) => setIntervalDays(Number(e.target.value))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-400 outline-none"
          >
            {INTERVAL_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-500 font-medium block mb-1">Fuente</label>
          <select
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-400 outline-none"
          >
            {SOURCE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-500 font-medium block mb-1">Fecha y hora de inicio</label>
          <input
            type="datetime-local"
            value={startAt}
            onChange={(e) => setStartAt(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-400 outline-none"
          />
        </div>
      </div>

      <div className="flex flex-wrap gap-2 pt-1">
        <button
          onClick={() => saveMutation.mutate()}
          disabled={saveMutation.isPending}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700 disabled:opacity-50 transition-colors"
        >
          {saveMutation.isPending ? 'Guardando...' : isActive ? 'Actualizar programación' : 'Activar programación'}
        </button>
        {isActive && (
          <button
            onClick={() => cancelMutation.mutate()}
            disabled={cancelMutation.isPending}
            className="px-4 py-2 border border-gray-300 text-gray-600 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50 transition-colors"
          >
            {cancelMutation.isPending ? 'Cancelando...' : 'Desactivar'}
          </button>
        )}
        {saved && (
          <span className="flex items-center gap-1 text-sm text-green-600 px-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Programación guardada
          </span>
        )}
      </div>
    </div>
  );
}

export default function ScrapingPage() {
  const queryClient = useQueryClient();
  const [source, setSource] = useState<'all' | 'gmaps' | 'bolivia'>('all');
  const [activeJob, setActiveJob] = useState<ScrapingJob | null>(null);
  const [runError, setRunError] = useState('');
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const { data: history, isLoading } = useQuery({
    queryKey: ['scrapingHistory'],
    queryFn: () => getScrapingHistory(30),
  });

  const startPolling = (jobId: string) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const job = await getScrapingStatus(jobId);
        setActiveJob(job);
        if (job.status !== 'running') {
          clearInterval(pollRef.current!);
          pollRef.current = null;
          queryClient.invalidateQueries({ queryKey: ['scrapingHistory'] });
        }
      } catch {
        clearInterval(pollRef.current!);
        pollRef.current = null;
      }
    }, 3000);
  };

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  async function handleRun() {
    setRunError('');
    setActiveJob(null);
    try {
      const { job_id } = await runScraper(source, true);
      const initial = await getScrapingStatus(job_id);
      setActiveJob(initial);
      startPolling(job_id);
    } catch (e: any) {
      setRunError(e?.response?.data?.detail || 'Error al iniciar el scraping');
    }
  }

  const chartData = history
    ? [...history.runs]
        .reverse()
        .slice(-15)
        .map((r) => ({
          label: new Date(r.imported_at).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' }),
          imported: r.records_imported ?? 0,
          skipped: r.records_skipped ?? 0,
        }))
    : [];

  const progress = activeJob && activeJob.steps_total > 0
    ? Math.round((activeJob.steps_done / activeJob.steps_total) * 100)
    : 0;

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-800">Scraping</h2>
        {history && (
          <span className="text-sm text-gray-500">
            Total en base de datos: <strong className="text-gray-700">{history.total_restaurants.toLocaleString()}</strong> restaurantes
          </span>
        )}
      </div>

      {/* Trigger */}
      <div className="bg-white rounded-xl p-5 shadow-sm space-y-4">
        <h3 className="text-sm font-semibold text-gray-700">Ejecutar Scraping</h3>
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="text-xs text-gray-500 font-medium block mb-1">Fuente</label>
            <select
              value={source}
              onChange={(e) => setSource(e.target.value as typeof source)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-400 outline-none"
              disabled={activeJob?.status === 'running'}
            >
              <option value="all">Todas las fuentes</option>
              <option value="gmaps">Google Maps</option>
              <option value="bolivia">Bolivia en tus Manos</option>
            </select>
          </div>
          <button
            onClick={handleRun}
            disabled={activeJob?.status === 'running'}
            className="flex items-center gap-2 px-5 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {activeJob?.status === 'running' ? (
              <>
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                En curso...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Iniciar Scraping
              </>
            )}
          </button>
        </div>

        {runError && (
          <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{runError}</p>
        )}

        {/* Job progress */}
        {activeJob && (
          <div className="border border-gray-100 rounded-lg p-4 space-y-2 bg-gray-50">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-700 font-medium truncate pr-4">{activeJob.current_step}</p>
              <StatusPill status={activeJob.status} />
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-primary-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="flex gap-4 text-xs text-gray-500">
              <span>{progress}% completado</span>
              {activeJob.status !== 'running' && (
                <>
                  <span>{activeJob.imported} importados</span>
                  <span>{activeJob.skipped} omitidos</span>
                </>
              )}
            </div>
            {activeJob.status !== 'running' && activeJob.message && (
              <p className={`text-xs ${activeJob.status === 'error' ? 'text-red-600' : 'text-green-700'}`}>
                {activeJob.message}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Scraping programado */}
      <ScheduleSection />

      {/* Chart */}
      {chartData.length > 0 && (
        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">
            Restaurantes importados por ejecución (últimas {chartData.length})
          </h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="imported" name="Importados" fill="#9B1C2E" radius={[4, 4, 0, 0]} stackId="a" />
              <Bar dataKey="skipped" name="Omitidos" fill="#E5E7EB" radius={[4, 4, 0, 0]} stackId="a" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* History table */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h3 className="text-sm font-semibold text-gray-700">Historial de Ejecuciones</h3>
        </div>
        {isLoading ? (
          <div className="p-6 text-center text-gray-400 text-sm">Cargando historial...</div>
        ) : !history || history.runs.length === 0 ? (
          <div className="p-6 text-center text-gray-400 text-sm">Sin ejecuciones registradas</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50">
                  <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Fecha</th>
                  <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Fuente</th>
                  <th className="text-right px-5 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Encontrados</th>
                  <th className="text-right px-5 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Importados</th>
                  <th className="text-right px-5 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Omitidos</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {history.runs.map((run) => (
                  <tr key={run.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-5 py-3 text-gray-600 whitespace-nowrap">
                      {new Date(run.imported_at).toLocaleString('es-ES', {
                        day: 'numeric', month: 'short', year: 'numeric',
                        hour: '2-digit', minute: '2-digit',
                      })}
                    </td>
                    <td className="px-5 py-3 text-gray-700">{sourceLabel(run.source_file)}</td>
                    <td className="px-5 py-3 text-right text-gray-600">{run.records_total ?? '—'}</td>
                    <td className="px-5 py-3 text-right font-medium text-green-700">{run.records_imported ?? '—'}</td>
                    <td className="px-5 py-3 text-right text-gray-400">{run.records_skipped ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
