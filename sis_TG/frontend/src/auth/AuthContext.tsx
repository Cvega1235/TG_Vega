import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import type { User, OTPResponse } from '../types/auth';
import { login as apiLogin, verifyOTP as apiVerifyOTP, getMe } from '../api/auth';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<OTPResponse>;
  verifyOTP: (otpToken: string, code: string) => Promise<void>;
  logout: () => void;
  hasRole: (minRole: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const ROLE_LEVELS: Record<string, number> = {
  superadmin: 4, admin: 3, analista: 2, viewer: 1,
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = sessionStorage.getItem('access_token');
    if (token) {
      getMe()
        .then(setUser)
        .catch(() => {
          sessionStorage.removeItem('access_token');
          sessionStorage.removeItem('refresh_token');
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string): Promise<OTPResponse> => {
    const response = await apiLogin({ email, password });
    return response;
  };

  const verifyOTP = async (otpToken: string, code: string): Promise<void> => {
    const tokens = await apiVerifyOTP({ otp_token: otpToken, code });
    sessionStorage.setItem('access_token', tokens.access_token);
    sessionStorage.setItem('refresh_token', tokens.refresh_token);
    const me = await getMe();
    setUser(me);
  };

  const logout = () => {
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('refresh_token');
    setUser(null);
  };

  const hasRole = (minRole: string): boolean => {
    if (!user) return false;
    return (ROLE_LEVELS[user.role] || 0) >= (ROLE_LEVELS[minRole] || 0);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, verifyOTP, logout, hasRole }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
