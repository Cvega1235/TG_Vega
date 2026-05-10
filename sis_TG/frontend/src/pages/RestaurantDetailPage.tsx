import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { MapContainer, TileLayer, Marker } from 'react-leaflet';
import { getRestaurant, getNotes, getHistory, addNote, updateRestaurantStatus } from '../api/restaurants';
import StatusBadge from '../components/common/StatusBadge';
import { ALL_STATUSES, STATUS_LABELS } from '../utils/constants';
import { useAuth } from '../auth/AuthContext';

export default function RestaurantDetailPage() {
  const { id } = useParams<{ id: string }>();
  const restaurantId = Number(id);
  const queryClient = useQueryClient();
  const { hasRole } = useAuth();
  const [noteContent, setNoteContent] = useState('');

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

  const statusMutation = useMutation({
    mutationFn: (status: string) => updateRestaurantStatus(restaurantId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant', restaurantId] });
      queryClient.invalidateQueries({ queryKey: ['history', restaurantId] });
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
          {hasRole('analista') && (
            <select
              value={restaurant.status}
              onChange={(e) => statusMutation.mutate(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-full sm:w-auto"
            >
              {ALL_STATUSES.map((s) => (
                <option key={s} value={s}>{STATUS_LABELS[s]}</option>
              ))}
            </select>
          )}
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
                  {score.total_score.toFixed(1)}
                </span>
                <span className="text-lg text-gray-400">/100</span>
              </div>
              <ScoreBar label="Afinidad Cocina" value={score.cuisine_score} max={30} color="bg-blue-500" />
              <ScoreBar label="Rating" value={score.rating_score} max={20} color="bg-yellow-500" />
              <ScoreBar label="Volumen Resenas" value={score.reviews_score} max={15} color="bg-green-500" />
              <ScoreBar label="Zona Premium" value={score.zone_score} max={15} color="bg-purple-500" />
              <ScoreBar label="Nivel Precio" value={score.price_score} max={10} color="bg-orange-500" />
              <ScoreBar label="Completitud Datos" value={score.completeness_score} max={10} color="bg-red-500" />
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
    </div>
  );
}

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
