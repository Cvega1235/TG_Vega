import { NavLink } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';

export default function Sidebar() {
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
    links.push({ to: '/users', label: 'Usuarios', icon: '👥', page: 'users' });
  }

  return (
    <aside className="w-64 min-h-screen flex flex-col animate-slide-in-left"
      style={{ background: 'linear-gradient(180deg, #4A0B0B 0%, #6B1414 50%, #7F1D1D 100%)' }}>

      {/* Logo */}
      <div className="p-6 border-b border-primary-700">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-primary-400 flex items-center justify-center text-white font-bold text-lg shadow-md">
            D
          </div>
          <div>
            <h1 className="text-lg font-bold text-white leading-tight">Don Piotr</h1>
            <p className="text-xs text-primary-200 mt-0.5">Inteligencia de Mercado</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-3 space-y-1 mt-2">
        {links.map(({ to, label, icon }, idx) => (
          <NavLink
            key={to}
            to={to}
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
}
