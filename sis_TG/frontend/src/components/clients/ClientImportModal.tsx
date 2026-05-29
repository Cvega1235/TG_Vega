import { useState, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import * as XLSX from 'xlsx';
import { bulkMatchClients, bulkApplyClients } from '../../api/restaurants';
import type { ClientMatch } from '../../api/restaurants';
import Portal from '../common/Portal';

interface Props {
  onClose: () => void;
}

type Step = 'input' | 'preview' | 'done';

interface ParsedRow {
  name: string;
  address: string;
}

function ConfidenceBadge({ match }: { match: ClientMatch }) {
  if (match.match_type === 'no_match')
    return <span className="text-xs px-2 py-0.5 rounded-full bg-red-50 text-red-600 border border-red-200">Sin coincidencia</span>;
  if (match.match_type === 'exact')
    return <span className="text-xs px-2 py-0.5 rounded-full bg-green-50 text-green-700 border border-green-200">Exacto</span>;
  const pct = Math.round(match.confidence * 100);
  const style = pct >= 85 ? 'bg-yellow-50 text-yellow-700 border-yellow-200' : 'bg-orange-50 text-orange-700 border-orange-200';
  return <span className={`text-xs px-2 py-0.5 rounded-full border ${style}`}>~{pct}%</span>;
}

async function parseFile(file: File): Promise<ParsedRow[]> {
  const buffer = await file.arrayBuffer();
  const wb = XLSX.read(buffer, { type: 'array' });
  const ws = wb.Sheets[wb.SheetNames[0]];
  const rows = XLSX.utils.sheet_to_json<unknown[]>(ws, { header: 1 });
  if (rows.length === 0) return [];

  // Detect if first row is a header (contains text like "nombre","name","dirección")
  const firstRow = (rows[0] as unknown[]).map((c) => String(c ?? '').toLowerCase().trim());
  const hasHeader = firstRow.some((h) => h.includes('nombre') || h.includes('name') || h.includes('direcc'));

  const dataRows = hasHeader ? rows.slice(1) : rows;

  // Column indices: name=0, address=1 (city=2 ignored)
  const nameIdx = hasHeader
    ? firstRow.findIndex((h) => h.includes('nombre') || h.includes('name'))
    : 0;
  const addrIdx = hasHeader
    ? firstRow.findIndex((h) => h.includes('direcc') || h.includes('address'))
    : 1;

  return dataRows
    .map((row) => {
      const cells = row as unknown[];
      const name = String(cells[nameIdx < 0 ? 0 : nameIdx] ?? '').trim();
      const address = String(cells[addrIdx < 0 ? 1 : addrIdx] ?? '').trim();
      return { name, address };
    })
    .filter((r) => r.name.length > 0);
}

const Spinner = () => (
  <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
  </svg>
);

export default function ClientImportModal({ onClose }: Props) {
  const queryClient = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);

  const [step, setStep] = useState<Step>('input');
  const [parsedRows, setParsedRows] = useState<ParsedRow[]>([]);
  const [matches, setMatches] = useState<ClientMatch[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [replaceMode, setReplaceMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<{ updated: number; already_client: number; demoted: number } | null>(null);

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setError('');
    try {
      const rows = await parseFile(file);
      setParsedRows(rows);
    } catch {
      setError('No se pudo leer el archivo. Verifica que sea un .xlsx válido.');
    }
    // reset input so same file can be re-selected
    e.target.value = '';
  }

  async function handlePreview() {
    if (parsedRows.length === 0) { setError('Sube un archivo primero.'); return; }
    setError('');
    setLoading(true);
    try {
      const names = parsedRows.map((r) => r.name);
      const data = await bulkMatchClients(names);
      setMatches(data);
      const preSelected = new Set(
        data
          .filter((m) => m.restaurant_id !== null && m.current_status !== 'cliente')
          .map((m) => m.restaurant_id!)
      );
      setSelected(preSelected);
      setStep('preview');
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Error al buscar coincidencias.');
    } finally {
      setLoading(false);
    }
  }

  async function handleApply() {
    setLoading(true);
    setError('');
    try {
      const ids = Array.from(selected);

      // Build address map: restaurantId → address from file
      const addressUpdates: Record<number, string> = {};
      matches.forEach((m, i) => {
        if (m.restaurant_id && selected.has(m.restaurant_id) && parsedRows[i]?.address) {
          addressUpdates[m.restaurant_id] = parsedRows[i].address;
        }
      });

      const data = await bulkApplyClients(ids, replaceMode, addressUpdates);
      setResult(data);
      setStep('done');
      queryClient.invalidateQueries({ queryKey: ['clients'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
      queryClient.invalidateQueries({ queryKey: ['clientHistory'] });
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Error al aplicar cambios.');
    } finally {
      setLoading(false);
    }
  }

  function toggleSelect(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  const matchCount = matches.filter((m) => m.restaurant_id !== null).length;
  const noMatchCount = matches.filter((m) => m.match_type === 'no_match').length;
  const alreadyClientCount = matches.filter((m) => m.current_status === 'cliente').length;

  return (
    <Portal>
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-4xl flex flex-col max-h-[90vh]">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div>
            <h2 className="text-base font-semibold text-gray-800">Importar Lista de Clientes</h2>
            {step === 'preview' && (
              <p className="text-xs text-gray-400 mt-0.5">
                {matchCount} coincidencias · {noMatchCount} sin resultado · {alreadyClientCount} ya son clientes
              </p>
            )}
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4">

          {/* Step: input */}
          {step === 'input' && (
            <div className="space-y-5">
              <p className="text-sm text-gray-600">
                Sube el archivo Excel con la lista de clientes. Se esperan 3 columnas:{' '}
                <strong>nombre</strong>, <strong>dirección</strong>, ciudad (ignorada).
              </p>

              <div
                onClick={() => fileRef.current?.click()}
                className="border-2 border-dashed border-gray-300 rounded-xl p-10 text-center cursor-pointer hover:border-primary-400 hover:bg-primary-50/30 transition-colors"
              >
                {parsedRows.length > 0 ? (
                  <div className="space-y-1">
                    <p className="text-2xl font-bold text-primary-600">{parsedRows.length}</p>
                    <p className="text-sm text-gray-600">registros cargados</p>
                    <p className="text-xs text-gray-400 mt-2">Haz clic para cambiar el archivo</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <svg className="w-10 h-10 text-gray-300 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                    </svg>
                    <p className="text-sm text-gray-500">Haz clic para subir el archivo</p>
                    <p className="text-xs text-gray-400">Formatos: .xlsx, .xls, .csv</p>
                  </div>
                )}
                <input ref={fileRef} type="file" accept=".xlsx,.xls,.csv" className="hidden" onChange={handleFileUpload} />
              </div>

              {parsedRows.length > 0 && (
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <p className="text-xs text-gray-500 px-3 py-2 bg-gray-50 border-b border-gray-200">
                    Vista previa (primeras 5 filas)
                  </p>
                  <table className="w-full text-xs">
                    <thead className="bg-gray-50 text-gray-500">
                      <tr>
                        <th className="px-3 py-1.5 text-left font-medium">Nombre</th>
                        <th className="px-3 py-1.5 text-left font-medium">Dirección</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {parsedRows.slice(0, 5).map((r, i) => (
                        <tr key={i}>
                          <td className="px-3 py-1.5 text-gray-700">{r.name}</td>
                          <td className="px-3 py-1.5 text-gray-500">{r.address || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {error && <p className="text-sm text-red-600">{error}</p>}
            </div>
          )}

          {/* Step: preview */}
          {step === 'preview' && (
            <div className="space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex gap-2 text-xs">
                  <button
                    onClick={() => setSelected(new Set(matches.filter(m => m.restaurant_id && m.current_status !== 'cliente').map(m => m.restaurant_id!)))}
                    className="text-primary-600 hover:underline"
                  >
                    Seleccionar todo
                  </button>
                  <span className="text-gray-300">·</span>
                  <button onClick={() => setSelected(new Set())} className="text-gray-500 hover:underline">Ninguno</button>
                </div>
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={replaceMode}
                    onChange={(e) => setReplaceMode(e.target.checked)}
                    className="accent-primary-600 w-4 h-4"
                  />
                  <span className="text-sm text-gray-700 font-medium">Reemplazar lista completa</span>
                  <span className="text-xs text-gray-400">(clientes no incluidos pasan a "contactado")</span>
                </label>
              </div>

              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
                    <tr>
                      <th className="px-3 py-2 w-8"></th>
                      <th className="px-3 py-2 text-left">Nombre en archivo</th>
                      <th className="px-3 py-2 text-left">Dirección</th>
                      <th className="px-3 py-2 text-left">Coincidencia en BD</th>
                      <th className="px-3 py-2 text-left">Estado actual</th>
                      <th className="px-3 py-2 text-left">Confianza</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {matches.map((m, i) => {
                      const isSelectable = m.restaurant_id !== null && m.current_status !== 'cliente';
                      const isChecked = m.restaurant_id !== null && selected.has(m.restaurant_id);
                      const rowAddress = parsedRows[i]?.address;
                      return (
                        <tr key={i} className={
                          m.match_type === 'no_match' ? 'bg-red-50/40' :
                          m.current_status === 'cliente' ? 'bg-green-50/40' : ''
                        }>
                          <td className="px-3 py-2 text-center">
                            {isSelectable ? (
                              <input type="checkbox" checked={isChecked}
                                onChange={() => toggleSelect(m.restaurant_id!)}
                                className="accent-primary-600" />
                            ) : (
                              <span className="text-gray-300">—</span>
                            )}
                          </td>
                          <td className="px-3 py-2 text-gray-700 font-medium">{m.input_name}</td>
                          <td className="px-3 py-2 text-gray-400 text-xs max-w-[160px] truncate" title={rowAddress}>
                            {rowAddress || '—'}
                          </td>
                          <td className="px-3 py-2 text-gray-600">
                            {m.restaurant_nombre ?? <span className="text-gray-400 italic">No encontrado</span>}
                          </td>
                          <td className="px-3 py-2">
                            {m.current_status ? (
                              <span className={`text-xs px-2 py-0.5 rounded-full ${m.current_status === 'cliente' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                                {m.current_status}
                              </span>
                            ) : '—'}
                          </td>
                          <td className="px-3 py-2"><ConfidenceBadge match={m} /></td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {replaceMode && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-sm text-amber-800">
                  <strong>Modo reemplazo activo:</strong> los clientes actuales que no estén en esta lista
                  pasarán automáticamente al estado <strong>"contactado"</strong>.
                </div>
              )}

              {error && <p className="text-sm text-red-600">{error}</p>}
            </div>
          )}

          {/* Step: done */}
          {step === 'done' && result && (
            <div className="py-8 text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto">
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div className="space-y-1">
                <p className="text-lg font-semibold text-gray-800">
                  {result.updated} restaurante{result.updated !== 1 ? 's' : ''} marcados como clientes
                </p>
                {result.already_client > 0 && (
                  <p className="text-sm text-gray-400">{result.already_client} ya eran clientes (sin cambios)</p>
                )}
                {result.demoted > 0 && (
                  <p className="text-sm text-amber-600">{result.demoted} clientes removidos de la lista → "contactado"</p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-100">
          <button
            onClick={step === 'input' ? onClose : step === 'done' ? onClose : () => setStep('input')}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            {step === 'preview' ? '← Volver' : step === 'done' ? 'Cerrar' : 'Cancelar'}
          </button>
          <div className="flex gap-3">
            {step === 'input' && (
              <button
                onClick={handlePreview}
                disabled={loading || parsedRows.length === 0}
                className="px-5 py-2 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2"
              >
                {loading && <Spinner />}
                Ver coincidencias →
              </button>
            )}
            {step === 'preview' && (
              <button
                onClick={handleApply}
                disabled={loading || selected.size === 0}
                className="px-5 py-2 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2"
              >
                {loading && <Spinner />}
                Actualizar {selected.size} cliente{selected.size !== 1 ? 's' : ''}
              </button>
            )}
            {step === 'done' && (
              <button onClick={onClose} className="px-5 py-2 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700">
                Cerrar
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
    </Portal>
  );
}
