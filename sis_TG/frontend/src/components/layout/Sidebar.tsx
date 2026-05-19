import { NavLink } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';
import logo from '../../assets/logo.svg';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { hasRole, hasPermission } = useAuth();

  const allLinks = [
    { to: '/dashboard',   label: 'Dashboard',    icon: '📊', page: 'dashboard' },
    { to: '/restaurants', label: 'Restaurantes', icon: '🍽️', page: 'restaurants' },
    { to: '/clients',     label: 'Clientes',     icon: '🤝', page: 'clients' },
    { to: '/ml-analysis', label: 'Analisis ML',  icon: '🧠', page: 'ml-analysis' },
    { to: '/reports',     label: 'Reportes',     icon: '📈', page: 'reports' },
  ];

  const links = allLinks.filter(({ page }) => hasPermission(page));
  if (hasRole('admin')) {
    links.push({ to: '/users',    label: 'Usuarios',  icon: '👥', page: 'users' });
    links.push({ to: '/scraping', label: 'Scraping',  icon: '🔍', page: 'scraping' });
    links.push({ to: '/security', label: 'Seguridad', icon: '🛡️', page: 'security' });
  }

  const sidebarContent = (
    <aside
      className="w-64 h-full flex flex-col animate-slide-in-left"
      style={{ background: 'linear-gradient(180deg, #4A0B0B 0%, #6B1414 50%, #7F1D1D 100%)' }}
    >
      {/* Logo */}
      <div className="p-6 border-b border-primary-700 flex items-center justify-center relative">
        <img src={logo} alt="Don Piotr" className="h-14 w-auto object-contain" />
        {/* Botón cerrar solo en móvil */}
        <button
          onClick={onClose}
          className="md:hidden text-primary-200 hover:text-white p-1 absolute right-4"
          aria-label="Cerrar menú"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-3 space-y-1 mt-2">
        {links.map(({ to, label, icon }, idx) => (
          <NavLink
            key={to}
            to={to}
            onClick={onClose}
            style={{ animationDelay: `${idx * 0.06}s` }}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 animate-fade-in
              ${isActive
                ? 'bg-white/15 text-white nav-active-glow shadow-sm'
                : 'text-primary-100 hover:bg-white/10 hover:text-white'
              }`
            }
          >
            <span className="text-base">{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-primary-700">
        <p className="text-xs text-primary-300 text-center">v1.0 · EMI 2026</p>
      </div>
    </aside>
  );

  return (
    <>
      {/* Desktop: siempre visible */}
      <div className="hidden md:flex w-64 min-h-screen shrink-0">
        {sidebarContent}
      </div>

      {/* Móvil: overlay cuando está abierto */}
      {isOpen && (
        <div className="fixed inset-0 z-40 md:hidden flex">
          <div className="absolute inset-0 bg-black/50" onClick={onClose} />
          <div className="relative z-50 h-full">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
}
