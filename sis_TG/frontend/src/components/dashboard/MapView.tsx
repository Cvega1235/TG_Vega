import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import type { MapDataPoint } from '../../types/dashboard';
import { useNavigate } from 'react-router-dom';

interface Props {
  data: MapDataPoint[] | undefined;
}

const STATUS_MARKER_COLORS: Record<string, string> = {
  nuevo: '#9ca3af',
  contactado: '#3b82f6',
  interesado: '#eab308',
  cliente: '#22c55e',
  no_interesado: '#ef4444',
};

function createIcon(status: string) {
  const color = STATUS_MARKER_COLORS[status] || '#9ca3af';
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="background:${color};width:12px;height:12px;border-radius:50%;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.3)"></div>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  });
}

export default function MapView({ data }: Props) {
  const navigate = useNavigate();

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm">
      <h3 className="text-sm font-medium text-gray-700 mb-4">Mapa de Restaurantes</h3>
      <div className="h-[400px] rounded-lg overflow-hidden">
        <MapContainer
          center={[-16.5, -68.15]}
          zoom={13}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {data?.map((point) => (
            <Marker
              key={point.id}
              position={[point.latitud, point.longitud]}
              icon={createIcon(point.status)}
            >
              <Popup>
                <div className="text-sm">
                  <p className="font-semibold">{point.nombre}</p>
                  {point.rating && <p>Rating: {point.rating}/5</p>}
                  {point.total_score && <p>Score: {point.total_score.toFixed(1)}</p>}
                  <button
                    onClick={() => navigate(`/restaurants/${point.id}`)}
                    className="text-primary-500 hover:underline mt-1 block"
                  >
                    Ver detalle
                  </button>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
      <div className="flex gap-4 mt-3 text-xs text-gray-500 flex-wrap">
        {Object.entries(STATUS_MARKER_COLORS).map(([status, color]) => (
          <div key={status} className="flex items-center gap-1">
            <div style={{ background: color, width: 10, height: 10, borderRadius: '50%' }} />
            <span className="capitalize">{status.replace('_', ' ')}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
