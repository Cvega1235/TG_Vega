import { useAuth } from '../../auth/AuthContext';
import { ROLE_LABELS } from '../../utils/constants';

export default function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
      <div />
      <div className="flex items-center gap-4">
        {user && (
          <>
            <div className="text-right">
              <p className="text-sm font-medium text-gray-700">{user.full_name}</p>
              <p className="text-xs text-gray-500">{ROLE_LABELS[user.role] || user.role}</p>
            </div>
            <button
              onClick={logout}
              className="px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            >
              Salir
            </button>
          </>
        )}
      </div>
    </header>
  );
}
