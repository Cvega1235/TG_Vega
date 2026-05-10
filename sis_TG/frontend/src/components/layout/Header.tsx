import { useAuth } from '../../auth/AuthContext';
import { ROLE_LABELS } from '../../utils/constants';

interface HeaderProps {
  onMenuToggle: () => void;
}

export default function Header({ onMenuToggle }: HeaderProps) {
  const { user, logout } = useAuth();

  return (
    <header className="bg-white border-b border-gray-100 px-4 sm:px-6 py-3 flex items-center justify-between shadow-sm animate-fade-in">
      <div className="flex items-center gap-3">
        {/* Hamburger — solo en móvil */}
        <button
          onClick={onMenuToggle}
          className="md:hidden p-1.5 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors"
          aria-label="Abrir menú"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <div className="hidden sm:flex items-center gap-2">
          <div className="w-1.5 h-6 rounded-full bg-primary-500" />
          <span className="text-sm text-gray-400 font-medium tracking-wide">Sistema de Inteligencia de Mercado</span>
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-4">
        {user && (
          <>
            <div className="text-right hidden sm:block">
              <p className="text-sm font-semibold text-gray-700">{user.full_name}</p>
              <p className="text-xs text-primary-500">{ROLE_LABELS[user.role] || user.role}</p>
            </div>
            <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-bold text-sm shrink-0">
              {user.full_name?.[0]?.toUpperCase() ?? 'U'}
            </div>
            <button
              onClick={logout}
              className="px-2.5 sm:px-3 py-1.5 text-sm text-primary-600 hover:bg-primary-50 rounded-lg transition-colors border border-primary-200 hover:border-primary-400"
            >
              Salir
            </button>
          </>
        )}
      </div>
    </header>
  );
}
