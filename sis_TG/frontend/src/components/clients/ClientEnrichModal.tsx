import { useEffect, useRef, useState } from 'react';
import { startEnrichment, getEnrichStatus, applyEnrichment } from '../../api/scraping';
import type { EnrichJob, EnrichResult, EnrichUpdate } from '../../api/scraping';

interface Props {
  onClose: () => void;
  onApplied: () => void;
}

const FIELD_LABELS: Record<string, string> = {
  telefono: 'Teléfono',
  latitud: 'Latitud',
  longitud: 'Longitud',
  rating: 'Rating',
  num_resenas: 'Reseñas',
  tipo_cocina: 'Tipo de cocina',
  website_url: 'Sitio web',
};

type Step = 'idle' | 'running' | 'review' | 'done' | 'error';

export default function ClientEnrichModal({ onClose, onApplied }: Props) {
  const [step, setStep] = useState<Step>('idle');
  const [job, setJob] = useState<EnrichJob | null>(null);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [applying, setApplying] = useState(false);
  const [appliedCount, setAppliedCount] = useState(0);
  const [errorMsg, setErrorMsg] = useState('');
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function stopPolling() {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }

  useEffect(() => () => stopPolling(), []);

  async function handleStart() {
    setStep('running');
    setErrorMsg('');
    try {
      const { job_id } = await startEnrichment(true);

      pollRef.current = setInterval(async () => {
        try {
          const status = await getEnrichStatus(job_id);
          setJob(status);
          if (status.status === 'completed') {
            stopPolling();
            const withData = status.results.filter((r) => r.found);
            setSelected(new Set(withData.map((r) => r.restaurant_id)));
            setStep('review');
          } else if (status.status === 'error') {
            stopPolling();
            setErrorMsg(status.message || 'Error desconocido');
            setStep('error');
          }
        } catch {
          stopPolling();
          setErrorMsg('Error consultando el estado del trabajo.');
          setStep('error');
        }
      }, 3000);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Error al iniciar el enriquecimiento.';
      setErrorMsg(msg);
      setStep('error');
    }
  }

  async function handleApply() {
    if (!job) return;
    setApplying(true);
    const updates: EnrichUpdate[] = job.results
      .filter((r) => r.found && selected.has(r.restaurant_id))
      .map((r) => ({ restaurant_id: r.restaurant_id, updates: r.updates }));

    try {
      const { applied } = await applyEnrichment(updates);
      setAppliedCount(applied);
      setStep('done');
      onApplied();
    } catch {
      setErrorMsg('Error aplicando los cambios.');
      setStep('error');
    } finally {
      setApplying(false);
    }
  }

  function toggleSelect(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  const foundResults = job?.results.filter((r) => r.found) ?? [];
  const progressPct =
    job && job.steps_total > 0
      ? Math.round((job.steps_done / job.steps_total) * 100)
      : 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-bold text-gray-900">Completar datos de clientes</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">

          {/* IDLE */}
          {step === 'idle' && (
            <div className="space-y-4 text-center py-4">
              <div className="text-4xl">🔍</div>
              <p className="text-gray-700 text-sm leading-relaxed max-w-md mx-auto">
                Se buscará en Google Maps información faltante (teléfono, coordenadas, rating,
                tipo de cocina y sitio web) para todos los clientes con datos incompletos.
                El proceso puede tardar varios minutos dependiendo del número de clientes.
              </p>
              <p className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 inline-block">
                Requiere conexión a internet y Google Chrome instalado.
              </p>
            </div>
          )}

          {/* RUNNING */}
          {step === 'running' && (
            <div className="space-y-4 py-4">
              <p className="text-sm font-medium text-gray-700 text-center">
                {job?.current_step ?? 'Iniciando búsqueda...'}
              </p>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-primary-600 h-3 rounded-full transition-all duration-500"
                  style={{ width: `${progressPct}%` }}
                />
              </div>
              <p className="text-center text-xs text-gray-500">
                {job ? `${job.steps_done} / ${job.steps_total} restaurantes` : 'Cargando...'}
              </p>
            </div>
          )}

          {/* REVIEW */}
          {step === 'review' && (
            <div className="space-y-3">
              {foundResults.length === 0 ? (
                <p className="text-center text-gray-500 py-6 text-sm">
                  No se encontraron datos nuevos para ningún cliente.
                </p>
              ) : (
                <>
                  <p className="text-sm text-gray-600">
                    Se encontraron datos nuevos para{' '}
                    <span className="font-semibold text-gray-900">{foundResults.length}</span>{' '}
                    cliente{foundResults.length !== 1 ? 's' : ''}.
                    Selecciona cuáles deseas actualizar:
                  </p>
                  <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                          <th className="w-10 px-3 py-2">
                            <input
                              type="checkbox"
                              checked={selected.size === foundResults.length}
                              onChange={(e) =>
                                setSelected(
                                  e.target.checked
                                    ? new Set(foundResults.map((r) => r.restaurant_id))
                                    : new Set(),
                                )
                              }
                            />
                          </th>
                          <th className="text-left px-3 py-2 font-semibold text-gray-600">Restaurante</th>
                          <th className="text-left px-3 py-2 font-semibold text-gray-600">Campos encontrados</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {foundResults.map((r) => (
                          <ResultRow
                            key={r.restaurant_id}
                            result={r}
                            checked={selected.has(r.restaurant_id)}
                            onToggle={() => toggleSelect(r.restaurant_id)}
                          />
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </div>
          )}

          {/* DONE */}
          {step === 'done' && (
            <div className="text-center py-6 space-y-2">
              <div className="text-4xl">✅</div>
              <p className="font-semibold text-gray-900">¡Listo!</p>
              <p className="text-sm text-gray-600">
                Se actualizaron <span className="font-semibold">{appliedCount}</span> restaurante
                {appliedCount !== 1 ? 's' : ''} con nuevos datos.
              </p>
            </div>
          )}

          {/* ERROR */}
          {step === 'error' && (
            <div className="text-center py-6 space-y-2">
              <div className="text-4xl">❌</div>
              <p className="text-sm text-red-600">{errorMsg}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            {step === 'done' ? 'Cerrar' : 'Cancelar'}
          </button>

          {step === 'idle' && (
            <button
              onClick={handleStart}
              className="px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              Iniciar búsqueda
            </button>
          )}

          {step === 'review' && foundResults.length > 0 && (
            <button
              onClick={handleApply}
              disabled={applying || selected.size === 0}
              className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors flex items-center gap-2"
            >
              {applying && (
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
              )}
              Aplicar {selected.size} cambio{selected.size !== 1 ? 's' : ''}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function ResultRow({
  result,
  checked,
  onToggle,
}: {
  result: EnrichResult;
  checked: boolean;
  onToggle: () => void;
}) {
  const fields = Object.keys(result.updates).filter((k) => result.updates[k as keyof typeof result.updates] != null);
  return (
    <tr className={checked ? 'bg-green-50' : ''}>
      <td className="px-3 py-2 text-center">
        <input type="checkbox" checked={checked} onChange={onToggle} />
      </td>
      <td className="px-3 py-2 font-medium text-gray-900">{result.restaurant_nombre}</td>
      <td className="px-3 py-2">
        <div className="flex flex-wrap gap-1">
          {fields.map((f) => (
            <span
              key={f}
              className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-0.5 rounded-full"
            >
              {FIELD_LABELS[f] ?? f}
            </span>
          ))}
        </div>
      </td>
    </tr>
  );
}
