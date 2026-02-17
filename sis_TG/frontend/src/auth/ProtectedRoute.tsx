import { Navigate } from 'react-router-dom';
import { useAuth } from './AuthContext';

interface Props {
  children: React.ReactNode;
  minRole?: string;
}

export default function ProtectedRoute({ children, minRole = 'viewer' }: Props) {
  const { user, loading, hasRole } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;
  if (!hasRole(minRole)) return <Navigate to="/dashboard" replace />;

  return <>{children}</>;
}
