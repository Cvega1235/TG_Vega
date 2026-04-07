import { NavLink } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';

export default function Sidebar() {
  const { hasRole, hasPermission } = useAuth();

  const allLinks = [
    { to: '/dashboard', label: 'Dashboard', icon: '📊', page: 'dashboard' },
    { to: '/restaurants', label: 'Restaurantes', icon: '🍽️', page: 'restaurants' },
    { to: '/clients', label: 'Clientes', icon: '🤝', page: 'clients' },
    { to: '/ml-analysis', label: 'Analisis ML', icon: '🧠', page: 'ml-analysis' },
    { to: '/reports', label: 'Reportes', icon: '📈', page: 'reports' },
  ];

  const links = allLinks.filter(({ page }) => hasPermission(page));

  if (hasRole('admin')) {
    links.push({ to: '/users', label: 'Usuarios', icon: '👥', page: 'users' });
  }

  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-screen flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-xl font-bold text-primary-700">Don Piotr</h1>
        <p className="text-xs text-gray-500 mt-1">Inteligencia de Mercado</p>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {links.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`
            }
          >
            <span>{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
