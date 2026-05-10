import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getUsers, createUser, updateUser, deleteUser } from '../api/users';
import { unlockUser } from '../api/security';
import { useAuth } from '../auth/AuthContext';
import { ROLE_LABELS, ROLE_LEVELS } from '../utils/constants';
import type { UserData, UserCreate } from '../types/user';

export default function UsersPage() {
  const queryClient = useQueryClient();
  const { user: currentUser } = useAuth();
  const [showForm, setShowForm] = useState(false);
  const [editingUser, setEditingUser] = useState<UserData | null>(null);

  const { data: users, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: getUsers,
  });

  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setShowForm(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteUser,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  });

  const unlockMutation = useMutation({
    mutationFn: unlockUser,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  });

  const currentLevel = ROLE_LEVELS[currentUser?.role || ''] || 0;
  const availableRoles = Object.entries(ROLE_LEVELS)
    .filter(([, level]) => level < currentLevel)
    .map(([role]) => role);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-800">Gestion de Usuarios</h2>
        <button
          onClick={() => { setEditingUser(null); setShowForm(true); }}
          className="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600"
        >
          Nuevo Usuario
        </button>
      </div>

      {/* Users table */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-400">Cargando...</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left py-3 px-4 text-gray-500 font-medium">Nombre</th>
                <th className="text-left py-3 px-4 text-gray-500 font-medium">Email</th>
                <th className="text-left py-3 px-4 text-gray-500 font-medium">Rol</th>
                <th className="text-left py-3 px-4 text-gray-500 font-medium">Estado</th>
                <th className="text-left py-3 px-4 text-gray-500 font-medium">Creado</th>
                <th className="text-left py-3 px-4 text-gray-500 font-medium">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {users?.map((u) => (
                <tr key={u.id} className="border-t border-gray-100">
                  <td className="py-3 px-4 font-medium text-gray-800">{u.full_name}</td>
                  <td className="py-3 px-4 text-gray-600">{u.email}</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-primary-50 text-primary-700">
                      {ROLE_LABELS[u.role] || u.role}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex flex-col gap-1">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium w-fit ${
                        u.is_active ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                      }`}>
                        {u.is_active ? 'Activo' : 'Inactivo'}
                      </span>
                      {(u as any).locked_until && new Date((u as any).locked_until) > new Date() && (
                        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-orange-50 text-orange-700 w-fit">
                          🔒 Bloqueado
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-4 text-gray-500 text-xs">
                    {new Date(u.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex gap-2 flex-wrap">
                      <button
                        onClick={() => { setEditingUser(u); setShowForm(true); }}
                        className="text-primary-500 hover:underline text-xs"
                      >
                        Editar
                      </button>
                      {(u as any).locked_until && new Date((u as any).locked_until) > new Date() && (
                        <button
                          onClick={() => unlockMutation.mutate(u.id)}
                          className="text-orange-600 hover:underline text-xs font-medium"
                        >
                          Desbloquear
                        </button>
                      )}
                      <button
                        onClick={() => {
                          if (confirm(`Desactivar a ${u.full_name}?`))
                            deleteMutation.mutate(u.id);
                        }}
                        className="text-red-500 hover:underline text-xs"
                      >
                        Desactivar
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Modal Form */}
      {showForm && (
        <UserFormModal
          user={editingUser}
          availableRoles={availableRoles}
          onClose={() => setShowForm(false)}
          onSubmit={(data) => {
            if (editingUser) {
              const { password, ...rest } = data;
              updateUser(editingUser.id, rest).then(() => {
                queryClient.invalidateQueries({ queryKey: ['users'] });
                setShowForm(false);
              });
            } else {
              createMutation.mutate(data);
            }
          }}
        />
      )}
    </div>
  );
}

const ALL_PAGES = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'restaurants', label: 'Restaurantes' },
  { key: 'clients', label: 'Clientes' },
  { key: 'ml-analysis', label: 'Analisis ML' },
  { key: 'reports', label: 'Reportes' },
];

function UserFormModal({
  user,
  availableRoles,
  onClose,
  onSubmit,
}: {
  user: UserData | null;
  availableRoles: string[];
  onClose: () => void;
  onSubmit: (data: UserCreate) => void;
}) {
  const [form, setForm] = useState<UserCreate>({
    email: user?.email || '',
    password: '',
    full_name: user?.full_name || '',
    role: user?.role || availableRoles[0] || 'viewer',
    permissions: user?.permissions ?? ALL_PAGES.map((p) => p.key),
  });

  const togglePermission = (key: string) => {
    const current = form.permissions ?? ALL_PAGES.map((p) => p.key);
    const updated = current.includes(key)
      ? current.filter((k) => k !== key)
      : [...current, key];
    setForm({ ...form, permissions: updated });
  };

  const allSelected = (form.permissions ?? []).length === ALL_PAGES.length;

  const toggleAll = () => {
    setForm({
      ...form,
      permissions: allSelected ? [] : ALL_PAGES.map((p) => p.key),
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-xl max-h-[90vh] overflow-y-auto">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          {user ? 'Editar Usuario' : 'Nuevo Usuario'}
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nombre completo</label>
            <input
              type="text"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
            />
          </div>
          {!user && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Contrasena</label>
              <input
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
              />
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Rol</label>
            <select
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
            >
              {availableRoles.map((r) => (
                <option key={r} value={r}>{ROLE_LABELS[r] || r}</option>
              ))}
            </select>
          </div>

          {/* Permisos por sección */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">
                Secciones visibles
              </label>
              <button
                type="button"
                onClick={toggleAll}
                className="text-xs text-primary-600 hover:underline"
              >
                {allSelected ? 'Quitar todas' : 'Seleccionar todas'}
              </button>
            </div>
            <div className="border border-gray-200 rounded-lg divide-y divide-gray-100">
              {ALL_PAGES.map(({ key, label }) => {
                const checked = (form.permissions ?? []).includes(key);
                return (
                  <label
                    key={key}
                    className="flex items-center gap-3 px-4 py-2.5 cursor-pointer hover:bg-gray-50"
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => togglePermission(key)}
                      className="w-4 h-4 accent-primary-600"
                    />
                    <span className="text-sm text-gray-700">{label}</span>
                    {!checked && (
                      <span className="ml-auto text-xs text-red-400">Sin acceso</span>
                    )}
                  </label>
                );
              })}
            </div>
            <p className="text-xs text-gray-400 mt-1">
              Los administradores siempre tienen acceso a todo sin importar esta configuracion.
            </p>
          </div>
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            Cancelar
          </button>
          <button
            onClick={() => onSubmit(form)}
            className="px-4 py-2 text-sm bg-primary-500 text-white rounded-lg hover:bg-primary-600"
          >
            {user ? 'Guardar' : 'Crear'}
          </button>
        </div>
      </div>
    </div>
  );
}
