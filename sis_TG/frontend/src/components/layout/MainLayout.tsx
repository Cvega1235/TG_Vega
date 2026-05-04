import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

export default function MainLayout() {
  const location = useLocation();

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <main key={location.pathname} className="flex-1 p-6 overflow-auto page-enter">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
