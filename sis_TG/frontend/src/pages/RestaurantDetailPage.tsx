import { useState } from 'react';
import { createPortal } from 'react-dom';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { MapContainer, TileLayer, Marker } from 'react-leaflet';
import { getRestaurant, getNotes, getHistory, addNote, updateRestaurantStatus, updateRestaurantRevenue } from '../api/restaurants';
import { getScoringWeights } from '../api/ml';
import StatusBadge from '../components/common/StatusBadge';
import ContactEmailModal from '../components/emails/ContactEmailModal';
import { ALL_STATUSES, STATUS_LABELS } from '../utils/constants';
import { useAuth } from '../auth/AuthContext';

export default function RestaurantDetailPage() {
  const { id } = useParams<{ id: string }>();
  const restaurantId = Number(id);
  const queryClient = useQueryClient();
  const { hasRole } = useAuth();
  const [noteContent, setNoteContent] = useState('');
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [revenueModalOpen, setRevenueModalOpen] = useState(false);
  const [pendingStatus, setPendingStatus] = useState<string | null>(null);
  const [productQty, setProductQty] = useState<Record<string, string>>({});
  const [editingRevenue, setEditingRevenue] = useState(false);
  const [editProductQty, setEditProductQty] = useState<Record<string, string>>({});

  const { data: restaurant, isLoading } = useQuery({
    queryKey: ['restaurant', restaurantId],
    queryFn: () => getRestaurant(restaurantId),
  });

  const { data: notes } = useQuery({
    queryKey: ['notes', restaurantId],
    queryFn: () => getNotes(restaurantId),
  });

  const { data: history } = useQuery({
    queryKey: ['history', restaurantId],
    queryFn: () => getHistory(restaurantId),
  });

  const { data: weights } = useQuery({
    queryKey: ['scoring-weights'],
    queryFn: getScoringWeights,
    staleTime: Infinity,
  });

  const statusMutation = useMutation({
    mutationFn: ({ status, monthly_revenue }: { status: string; monthly_revenue?: number }) =>
      updateRestaurantStatus(restaurantId, status, monthly_revenue),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant', restaurantId] });
      queryClient.invalidateQueries({ queryKey: ['history', restaurantId] });
      queryClient.invalidateQueries({ queryKey: ['kpiEvolution'] });
      queryClient.invalidateQueries({ queryKey: ['clientHistory'] });
      queryClient.invalidateQueries({ queryKey: ['clients'] });
      queryClient.invalidateQueries({ queryKey: ['restaurants'] });
    },
  });

  const revenueMutation = useMutation({
    mutationFn: (monthly_revenue: number) => updateRestaurantRevenue(restaurantId, monthly_revenue),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant', restaurantId] });
      queryClient.invalidateQueries({ queryKey: ['kpiEvolution'] });
      setEditingRevenue(false);
    },
  });

  const noteMutation = useMutation({
    mutationFn: (content: string) => addNote(restaurantId, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes', restaurantId] });
      setNoteContent('');
    },
  });

  if (isLoading || !restaurant) {
    return <div className="text-center py-8 text-gray-400">Cargando...</div>;
  }

  const score = restaurant.score;
  const mlScore = restaurant.ml_score ?? null;
  const displayScore = mlScore?.composite_score ?? score?.total_score ?? null;

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div className="bg-white rounded-xl p-5 sm:p-6 shadow-sm">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-gray-800">{restaurant.nombre}</h2>
            <div className="flex items-center gap-3 mt-2">
              <span className="text-sm text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                {restaurant.fuente}
              </span>
              <StatusBadge status={restaurant.status} />
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {hasRole('analista') && (
              <button
                onClick={() => setShowEmailModal(true)}
                className="flex items-center gap-1.5 px-4 py-2 border border-primary-300 text-primary-600 rounded-lg text-sm hover:bg-primary-50 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                Enviar Email
              </button>
            )}
            {hasRole('analista') && (
              <select
                value={restaurant.status}
                onChange={(e) => {
                  const newStatus = e.target.value;
                  if (newStatus === 'cliente' && restaurant.status !== 'cliente') {
                    setPendingStatus(newStatus);
                    setProductQty({});
                    setRevenueModalOpen(true);
                  } else {
                    statusMutation.mutate({ status: newStatus });
                  }
                }}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-full sm:w-auto"
              >
                {ALL_STATUSES.map((s) => (
                  <option key={s} value={s}>{STATUS_LABELS[s]}</option>
                ))}
              </select>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Info */}
        <div className="bg-white rounded-xl p-6 shadow-sm space-y-3">
          <h3 className="text-lg font-semibold text-gray-700">Informacion</h3>
          <InfoRow label="Direccion" value={restaurant.direccion} />
          <InfoRow label="Telefono" value={restaurant.telefono} />
          <InfoRow label="Rating" value={restaurant.rating ? `${restaurant.rating}/5` : null} />
          <InfoRow label="Resenas" value={restaurant.num_resenas?.toString()} />
          <InfoRow label="Tipo Cocina" value={restaurant.tipo_cocina} />
          <InfoRow label="Precio" value={restaurant.precio} />
          <InfoRow label="Zona" value={restaurant.zona} />
          <InfoRow label="Categoria" value={restaurant.categoria} />
          <InfoRow label="Servicios" value={restaurant.servicios} />
          {restaurant.descripcion && (
            <div>
              <span className="text-sm text-gray-500">Descripcion:</span>
              <p className="text-sm text-gray-700 mt-1">{restaurant.descripcion}</p>
            </div>
          )}
          {restaurant.url && (
            <a
              href={restaurant.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary-500 hover:underline block mt-2"
            >
              Ver en fuente original
            </a>
          )}
        </div>

        {/* Score */}
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-700 mb-4">Score de Cliente Potencial</h3>
          {score ? (
            <div className="space-y-3">
              <div className="text-center mb-4">
                <span className="text-4xl font-bold text-primary-600">
                  {displayScore != null ? displayScore.toFixed(1) : score.total_score.toFixed(1)}
                </span>
                <span className="text-lg text-gray-400">/100</span>
                <div className="mt-1">
                  {mlScore?.composite_score != null ? (
                    <span className="text-xs text-green-600 font-medium bg-green-50 px-2 py-0.5 rounded-full">Score ML</span>
                  ) : (
                    <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">Score heurístico</span>
                  )}
                </div>
              </div>
              <ScoreBar label="Afinidad Cocina" value={score.cuisine_score} max={weights?.w_cuisine ?? 30} color="bg-blue-500" />
              <ScoreBar label="Rating" value={score.rating_score} max={weights?.w_rating ?? 20} color="bg-yellow-500" />
              <ScoreBar label="Volumen Resenas" value={score.reviews_score} max={weights?.w_reviews ?? 15} color="bg-green-500" />
              <ScoreBar label="Zona Premium" value={score.zone_score} max={weights?.w_zone ?? 15} color="bg-purple-500" />
              <ScoreBar label="Nivel Precio" value={score.price_score} max={weights?.w_price ?? 10} color="bg-orange-500" />
              <ScoreBar label="Completitud Datos" value={score.completeness_score} max={weights?.w_completeness ?? 10} color="bg-red-500" />
              {score.conversion_probability != null && (
                <div className="mt-4 pt-3 border-t border-gray-100">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Prob. conversión (ML)</span>
                    <span className={`text-sm font-bold px-2.5 py-0.5 rounded-full ${
                      score.conversion_probability >= 0.75
                        ? 'bg-green-100 text-green-800'
                        : score.conversion_probability >= 0.5
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {Math.round(score.conversion_probability * 100)}%
                    </span>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">Score no calculado</p>
          )}
        </div>
      </div>

      {/* Map */}
      {restaurant.latitud && restaurant.longitud && (
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-700 mb-4">Ubicacion</h3>
          <div className="h-[300px] rounded-lg overflow-hidden">
            <MapContainer
              center={[restaurant.latitud, restaurant.longitud]}
              zoom={16}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer
                attribution='&copy; OpenStreetMap'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <Marker position={[restaurant.latitud, restaurant.longitud]} />
            </MapContainer>
          </div>
        </div>
      )}

      {/* Notes */}
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-700 mb-4">Notas</h3>
        {hasRole('analista') && (
          <div className="flex gap-2 mb-4">
            <input
              type="text"
              value={noteContent}
              onChange={(e) => setNoteContent(e.target.value)}
              placeholder="Agregar una nota..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && noteContent.trim()) {
                  noteMutation.mutate(noteContent.trim());
                }
              }}
            />
            <button
              onClick={() => noteContent.trim() && noteMutation.mutate(noteContent.trim())}
              disabled={noteMutation.isPending || !noteContent.trim()}
              className="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm hover:bg-primary-600 disabled:opacity-50"
            >
              Agregar
            </button>
          </div>
        )}
        <div className="space-y-3">
          {notes?.length ? (
            notes.map((note) => (
              <div key={note.id} className="border-l-2 border-primary-200 pl-3 py-1">
                <p className="text-sm text-gray-700">{note.content}</p>
                <p className="text-xs text-gray-400 mt-1">
                  {note.user_name} - {new Date(note.created_at).toLocaleString()}
                </p>
              </div>
            ))
          ) : (
            <p className="text-sm text-gray-400">Sin notas</p>
          )}
        </div>
      </div>

      {/* History */}
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-700 mb-4">Historial de Estados</h3>
        <div className="space-y-2">
          {history?.length ? (
            history.map((change) => (
              <div key={change.id} className="flex flex-wrap items-center gap-2 text-sm">
                <span className="text-gray-400 text-xs">
                  {new Date(change.changed_at).toLocaleString()}
                </span>
                {change.old_status && (
                  <>
                    <StatusBadge status={change.old_status} />
                    <span className="text-gray-400">→</span>
                  </>
                )}
                <StatusBadge status={change.new_status} />
                <span className="text-gray-500 text-xs">por {change.user_name}</span>
              </div>
            ))
          ) : (
            <p className="text-sm text-gray-400">Sin cambios de estado</p>
          )}
        </div>
      </div>

      {/* Revenue card — only for active clients */}
      {restaurant.status === 'cliente' && hasRole('analista') && (
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-700">Ingresos del Cliente</h3>
            <button
              onClick={() => {
                setEditProductQty({});
                setEditingRevenue(true);
              }}
              className="text-xs text-primary-600 hover:underline"
            >
              Editar
            </button>
          </div>
          <div>
            <p className="text-3xl font-bold text-gray-800 tabular-nums">
              {restaurant.monthly_revenue != null
                ? `${restaurant.monthly_revenue.toLocaleString('es-BO', { minimumFractionDigits: 2 })} Bs`
                : <span className="text-gray-400 text-base font-normal">Sin valor registrado</span>
              }
            </p>
            <p className="text-xs text-gray-400 mt-1">
              {restaurant.monthly_revenue != null ? 'Ingreso mensual estimado / real' : 'No se ha ingresado aún'}
            </p>
          </div>
        </div>
      )}

      {showEmailModal && (
        <ContactEmailModal
          restaurantId={restaurantId}
          restaurantName={restaurant.nombre}
          onClose={() => setShowEmailModal(false)}
        />
      )}

      {/* Revenue modal — shown when converting a restaurant to 'cliente' */}
      {revenueModalOpen && createPortal(
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl flex flex-col max-h-[90vh]">
            <div className="p-6 pb-4 border-b border-gray-100">
              <h3 className="text-lg font-semibold text-gray-800">Nuevo cliente</h3>
              <p className="text-sm text-gray-500 mt-1">
                Registra los productos y cantidades mensuales para <span className="font-medium">{restaurant.nombre}</span>.
              </p>
            </div>
            <div className="overflow-y-auto flex-1 p-6 pt-4">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-gray-500 uppercase border-b border-gray-200">
                    <th className="text-left pb-2 font-medium">Producto</th>
                    <th className="text-center pb-2 font-medium">Precio (Bs./kg)</th>
                    <th className="text-center pb-2 font-medium">Kg / mes</th>
                    <th className="text-right pb-2 font-medium">Total (Bs.)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {DON_PIOTR_PRODUCTS.map(({ nombre, precio }) => {
                    const kg = parseFloat(productQty[nombre] ?? '') || 0;
                    const subtotal = kg * precio;
                    return (
                      <tr key={nombre}>
                        <td className="py-2.5 pr-4 text-gray-700 font-medium">{nombre}</td>
                        <td className="py-2.5 text-center text-gray-500">{precio}</td>
                        <td className="py-2.5 px-3">
                          <input
                            type="number"
                            min="0"
                            step="0.5"
                            value={productQty[nombre] ?? ''}
                            onChange={(e) =>
                              setProductQty((prev) => ({ ...prev, [nombre]: e.target.value }))
                            }
                            placeholder="0"
                            className="w-24 px-2 py-1 border border-gray-300 rounded-md text-sm text-center focus:ring-2 focus:ring-primary-500 outline-none mx-auto block"
                          />
                        </td>
                        <td className="py-2.5 text-right text-gray-700 tabular-nums">
                          {subtotal > 0
                            ? subtotal.toLocaleString('es-BO', { minimumFractionDigits: 2 })
                            : '—'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
                <tfoot>
                  <tr className="border-t-2 border-gray-300">
                    <td colSpan={3} className="pt-3 text-sm font-semibold text-gray-800 uppercase tracking-wide">
                      Total mensual
                    </td>
                    <td className="pt-3 text-right text-base font-bold text-primary-600 tabular-nums">
                      {(() => {
                        const total = DON_PIOTR_PRODUCTS.reduce((sum, { nombre, precio }) => {
                          const kg = parseFloat(productQty[nombre] ?? '') || 0;
                          return sum + kg * precio;
                        }, 0);
                        return total > 0
                          ? `${total.toLocaleString('es-BO', { minimumFractionDigits: 2 })} Bs.`
                          : '0.00 Bs.';
                      })()}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
            <div className="p-6 pt-4 border-t border-gray-100 flex justify-end gap-2">
              <button
                onClick={() => {
                  setRevenueModalOpen(false);
                  setPendingStatus(null);
                }}
                className="px-4 py-2 border border-gray-300 text-gray-600 rounded-lg text-sm hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={() => {
                  const total = DON_PIOTR_PRODUCTS.reduce((sum, { nombre, precio }) => {
                    const kg = parseFloat(productQty[nombre] ?? '') || 0;
                    return sum + kg * precio;
                  }, 0);
                  if (total > 0 && pendingStatus) {
                    statusMutation.mutate({ status: pendingStatus, monthly_revenue: total });
                    setRevenueModalOpen(false);
                  }
                }}
                disabled={DON_PIOTR_PRODUCTS.every(({ nombre }) => !parseFloat(productQty[nombre] ?? ''))}
                className="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm hover:bg-primary-600 disabled:opacity-50"
              >
                Confirmar
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* Edit revenue modal — same product table, saves via revenueMutation */}
      {editingRevenue && createPortal(
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl flex flex-col max-h-[90vh]">
            <div className="p-6 pb-4 border-b border-gray-100">
              <h3 className="text-lg font-semibold text-gray-800">Editar ingresos del cliente</h3>
              <p className="text-sm text-gray-500 mt-1">
                Actualiza los productos y cantidades mensuales para{' '}
                <span className="font-medium">{restaurant.nombre}</span>.
              </p>
            </div>
            <div className="overflow-y-auto flex-1 p-6 pt-4">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-gray-500 uppercase border-b border-gray-200">
                    <th className="text-left pb-2 font-medium">Producto</th>
                    <th className="text-center pb-2 font-medium">Precio (Bs./kg)</th>
                    <th className="text-center pb-2 font-medium">Kg / mes</th>
                    <th className="text-right pb-2 font-medium">Total (Bs.)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {DON_PIOTR_PRODUCTS.map(({ nombre, precio }) => {
                    const kg = parseFloat(editProductQty[nombre] ?? '') || 0;
                    const subtotal = kg * precio;
                    return (
                      <tr key={nombre}>
                        <td className="py-2.5 pr-4 text-gray-700 font-medium">{nombre}</td>
                        <td className="py-2.5 text-center text-gray-500">{precio}</td>
                        <td className="py-2.5 px-3">
                          <input
                            type="number"
                            min="0"
                            step="0.5"
                            value={editProductQty[nombre] ?? ''}
                            onChange={(e) =>
                              setEditProductQty((prev) => ({ ...prev, [nombre]: e.target.value }))
                            }
                            placeholder="0"
                            className="w-24 px-2 py-1 border border-gray-300 rounded-md text-sm text-center focus:ring-2 focus:ring-primary-500 outline-none mx-auto block"
                          />
                        </td>
                        <td className="py-2.5 text-right text-gray-700 tabular-nums">
                          {subtotal > 0
                            ? subtotal.toLocaleString('es-BO', { minimumFractionDigits: 2 })
                            : '—'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
                <tfoot>
                  <tr className="border-t-2 border-gray-300">
                    <td colSpan={3} className="pt-3 text-sm font-semibold text-gray-800 uppercase tracking-wide">
                      Total mensual
                    </td>
                    <td className="pt-3 text-right text-base font-bold text-primary-600 tabular-nums">
                      {(() => {
                        const total = DON_PIOTR_PRODUCTS.reduce((sum, { nombre, precio }) => {
                          const kg = parseFloat(editProductQty[nombre] ?? '') || 0;
                          return sum + kg * precio;
                        }, 0);
                        return total > 0
                          ? `${total.toLocaleString('es-BO', { minimumFractionDigits: 2 })} Bs.`
                          : '0.00 Bs.';
                      })()}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
            <div className="p-6 pt-4 border-t border-gray-100 flex justify-end gap-2">
              <button
                onClick={() => setEditingRevenue(false)}
                className="px-4 py-2 border border-gray-300 text-gray-600 rounded-lg text-sm hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={() => {
                  const total = DON_PIOTR_PRODUCTS.reduce((sum, { nombre, precio }) => {
                    const kg = parseFloat(editProductQty[nombre] ?? '') || 0;
                    return sum + kg * precio;
                  }, 0);
                  if (total > 0) {
                    revenueMutation.mutate(total);
                    setEditingRevenue(false);
                  }
                }}
                disabled={
                  revenueMutation.isPending ||
                  DON_PIOTR_PRODUCTS.every(({ nombre }) => !parseFloat(editProductQty[nombre] ?? ''))
                }
                className="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm hover:bg-primary-600 disabled:opacity-50"
              >
                Guardar
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}

const DON_PIOTR_PRODUCTS: { nombre: string; precio: number }[] = [
  { nombre: 'Kielbasa',           precio: 60  },
  { nombre: 'Chorizo Parrillero', precio: 54  },
  { nombre: 'Jamón Inglés',       precio: 60  },
  { nombre: 'Costilla Ahumada',   precio: 68  },
  { nombre: 'Jamón Ahumado',      precio: 68  },
  { nombre: 'Jamón Crudo',        precio: 120 },
  { nombre: 'Tocino',             precio: 70  },
  { nombre: 'Salame',             precio: 55  },
  { nombre: 'Cabanosy',           precio: 65  },
];

function InfoRow({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) return null;
  return (
    <div className="flex justify-between text-sm">
      <span className="text-gray-500">{label}</span>
      <span className="text-gray-700 font-medium text-right max-w-[60%]">{value}</span>
    </div>
  );
}

function ScoreBar({ label, value, max, color }: { label: string; value: number | null; max: number; color: string }) {
  const v = value || 0;
  const pct = (v / max) * 100;
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-500">{label}</span>
        <span className="text-gray-700 font-medium">{v.toFixed(1)}/{max}</span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-2">
        <div className={`${color} rounded-full h-2 transition-all`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
