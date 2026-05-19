import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { getRestaurants } from '../api/restaurants';
import ClientImportModal from '../components/clients/ClientImportModal';
import { useAuth } from '../auth/AuthContext';

export default function ClientsPage() {
  const navigate = useNavigate();
  const { hasRole } = useAuth();
  const [search, setSearch] = useState('');
  const [zona, setZona] = useState('');
  const [page, setPage] = useState(1);
  const [showImport, setShowImport] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['clients', search, zona, page],
    queryFn: () =>
      getRestaurants({
        status: 'cliente',
        search: search || undefined,
        zona: zona || undefined,
        page,
        per_page: 20,
        sort_by: 'nombre',
        sort_order: 'asc',
      }),
  });

  const clients = data?.items ?? [];
  const total = data?.total ?? 0;
  const pages = data?.pages ?? 1;

  const zonas = Array.from(new Set(clients.map((c) => c.zona).filter(Boolean))) as string[];

  return (
    <div className="space-y-6">
      {/* Encabezado */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Clientes Actuales</h1>
          <p className="text-sm text-gray-500 mt-1">
            Restaurantes que actualmente son clientes de Don Piotr
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="bg-green-100 text-green-800 text-sm font-semibold px-4 py-2 rounded-full">
            {total} cliente{total !== 1 ? 's' : ''}
          </span>
          {hasRole('analista') && (
            <button
              onClick={() => setShowImport(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              Importar lista
            </button>
          )}
        </div>
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 flex flex-wrap gap-4">
        <div className="flex-1 min-w-48">
          <label className="block text-xs font-medium text-gray-500 mb-1">Buscar</label>
          <input
            type="text"
            placeholder="Nombre o dirección..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        <div className="w-48">
          <label className="block text-xs font-medium text-gray-500 mb-1">Zona</label>
          <select
            value={zona}
            onChange={(e) => { setZona(e.target.value); setPage(1); }}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">Todas las zonas</option>
            {zonas.map((z) => (
              <option key={z} value={z}>{z}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Tabla */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-gray-400">Cargando clientes...</div>
        ) : clients.length === 0 ? (
          <div className="p-12 text-center text-gray-400">
            No se encontraron clientes con los filtros aplicados.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-3 sm:px-4 py-3 font-semibold text-gray-600 hidden sm:table-cell">#</th>
                  <th className="text-left px-3 sm:px-4 py-3 font-semibold text-gray-600">Nombre</th>
                  <th className="text-left px-3 sm:px-4 py-3 font-semibold text-gray-600 hidden sm:table-cell">Zona</th>
                  <th className="text-left px-3 sm:px-4 py-3 font-semibold text-gray-600 hidden md:table-cell">Tipo de Cocina</th>
                  <th className="text-left px-3 sm:px-4 py-3 font-semibold text-gray-600">Rating</th>
                  <th className="text-left px-3 sm:px-4 py-3 font-semibold text-gray-600 hidden md:table-cell">Reseñas</th>
                  <th className="text-left px-3 sm:px-4 py-3 font-semibold text-gray-600 hidden lg:table-cell">Teléfono</th>
                  <th className="text-left px-3 sm:px-4 py-3 font-semibold text-gray-600 hidden lg:table-cell">Embutidos</th>
                  <th className="text-left px-3 sm:px-4 py-3 font-semibold text-gray-600 hidden sm:table-cell">Score ML</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {clients.map((client, idx) => (
                  <tr
                    key={client.id}
                    onClick={() => navigate(`/restaurants/${client.id}`)}
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <td className="px-3 sm:px-4 py-3 text-gray-400 text-xs hidden sm:table-cell">
                      {(page - 1) * 20 + idx + 1}
                    </td>
                    <td className="px-3 sm:px-4 py-3 font-medium text-gray-900">
                      <span className="block">{client.nombre}</span>
                      <span className="text-xs text-gray-400 sm:hidden">{client.zona ?? ''}</span>
                    </td>
                    <td className="px-3 sm:px-4 py-3 text-gray-600 hidden sm:table-cell">{client.zona ?? '—'}</td>
                    <td className="px-3 sm:px-4 py-3 text-gray-600 hidden md:table-cell">{client.tipo_cocina ?? '—'}</td>
                    <td className="px-3 sm:px-4 py-3">
                      {client.rating != null ? (
                        <span className="flex items-center gap-1">
                          <span className="text-yellow-500">★</span>
                          <span className="font-medium">{client.rating.toFixed(1)}</span>
                        </span>
                      ) : '—'}
                    </td>
                    <td className="px-3 sm:px-4 py-3 text-gray-600 hidden md:table-cell">
                      {client.num_resenas != null ? client.num_resenas.toLocaleString() : '—'}
                    </td>
                    <td className="px-3 sm:px-4 py-3 text-gray-600 hidden lg:table-cell">{client.telefono ?? '—'}</td>
                    <td className="px-3 sm:px-4 py-3 hidden lg:table-cell">
                      {(client as any).tiene_embutidos === true ? (
                        <span className="text-green-600 font-medium">✓ Sí</span>
                      ) : (client as any).tiene_embutidos === false ? (
                        <span className="text-gray-400">No</span>
                      ) : (
                        <span className="text-gray-300">—</span>
                      )}
                    </td>
                    <td className="px-3 sm:px-4 py-3 hidden sm:table-cell">
                      {client.score?.total_score != null ? (
                        <span className="bg-green-100 text-green-800 text-xs font-semibold px-2 py-1 rounded-full">
                          {client.score.total_score}
                        </span>
                      ) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showImport && <ClientImportModal onClose={() => setShowImport(false)} />}

      {/* Paginación */}
      {pages > 1 && (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between text-sm text-gray-600">
          <span>{total} clientes en total</span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 rounded border border-gray-300 disabled:opacity-40 hover:bg-gray-50"
            >
              ← Anterior
            </button>
            <span className="px-3 py-1">
              Página {page} de {pages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(pages, p + 1))}
              disabled={page === pages}
              className="px-3 py-1 rounded border border-gray-300 disabled:opacity-40 hover:bg-gray-50"
            >
              Siguiente →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
