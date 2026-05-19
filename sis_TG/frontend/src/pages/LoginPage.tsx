import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import logo from '../assets/logo.svg';

export default function LoginPage() {
  const [step, setStep] = useState<'credentials' | 'otp'>('credentials');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const [otpToken, setOtpToken] = useState('');
  const [maskedEmail, setMaskedEmail] = useState('');
  const [otpDigits, setOtpDigits] = useState(['', '', '', '', '', '']);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const { login, verifyOTP } = useAuth();
  const navigate = useNavigate();

  const handleCredentialsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const response = await login(email, password);
      setOtpToken(response.otp_token);
      setMaskedEmail(response.email);
      setStep('otp');
    } catch {
      setError('Email o contrasena incorrectos');
    } finally {
      setLoading(false);
    }
  };

  const handleOTPSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const code = otpDigits.join('');
    if (code.length !== 6) {
      setError('Ingresa el codigo completo de 6 digitos');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await verifyOTP(otpToken, code);
      navigate('/dashboard');
    } catch {
      setError('Codigo incorrecto o expirado');
    } finally {
      setLoading(false);
    }
  };

  const handleDigitChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;
    const newDigits = [...otpDigits];
    newDigits[index] = value.slice(-1);
    setOtpDigits(newDigits);
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otpDigits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (pasted.length === 6) {
      setOtpDigits(pasted.split(''));
      inputRefs.current[5]?.focus();
    }
  };

  useEffect(() => {
    if (step === 'otp') {
      inputRefs.current[0]?.focus();
    }
  }, [step]);

  const handleBackToLogin = () => {
    setStep('credentials');
    setOtpDigits(['', '', '', '', '', '']);
    setError('');
    setOtpToken('');
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden"
      style={{ background: 'linear-gradient(135deg, #4A0B0B 0%, #7F1D1D 50%, #9B1C2E 100%)' }}>

      {/* Decorative circles */}
      <div className="absolute top-[-80px] right-[-80px] w-72 h-72 rounded-full opacity-10"
        style={{ background: 'radial-gradient(circle, #FF8FA3, transparent)' }} />
      <div className="absolute bottom-[-60px] left-[-60px] w-56 h-56 rounded-full opacity-10"
        style={{ background: 'radial-gradient(circle, #FF8FA3, transparent)' }} />

      <div className="max-w-md w-full mx-4 animate-scale-in">
        {/* Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8 relative overflow-hidden">
          {/* Top accent bar */}
          <div className="absolute top-0 left-0 right-0 h-1 rounded-t-2xl"
            style={{ background: 'linear-gradient(90deg, #9B1C2E, #C94B6A)' }} />

          <div className="text-center mb-5">
            <img src={logo} alt="Don Piotr" className="w-28 h-28 object-contain mx-auto mb-2 animate-fade-in" />
            <h1 className="text-2xl font-bold text-gray-800">Don Piotr</h1>
            <p className="text-gray-400 text-sm mt-1">Sistema de Inteligencia de Mercado</p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 p-3 rounded-lg text-sm mb-5 animate-fade-in">
              {error}
            </div>
          )}

          {step === 'credentials' ? (
            <form onSubmit={handleCredentialsSubmit} className="space-y-5">
              <div className="animate-fade-in" style={{ animationDelay: '0.1s' }}>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-300 focus:border-primary-400 outline-none transition-all"
                  placeholder="admin@donpiotr.com"
                  required
                />
              </div>
              <div className="animate-fade-in" style={{ animationDelay: '0.15s' }}>
                <label className="block text-sm font-medium text-gray-700 mb-1">Contrasena</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-300 focus:border-primary-400 outline-none transition-all"
                  placeholder="••••••••"
                  required
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full text-white py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50 animate-fade-in"
                style={{ animationDelay: '0.2s', background: 'linear-gradient(90deg, #7F1D1D, #9B1C2E)' }}
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                    </svg>
                    Verificando...
                  </span>
                ) : 'Ingresar'}
              </button>
            </form>
          ) : (
            <form onSubmit={handleOTPSubmit} className="space-y-5">
              <div className="text-center mb-2 animate-fade-in">
                <div className="w-16 h-16 bg-primary-50 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <p className="text-gray-500 text-sm">Enviamos un codigo de verificacion a</p>
                <p className="font-semibold text-gray-800 mt-1">{maskedEmail}</p>
              </div>

              <div className="flex justify-center gap-2 animate-fade-in" onPaste={handlePaste}
                style={{ animationDelay: '0.1s' }}>
                {otpDigits.map((digit, i) => (
                  <input
                    key={i}
                    ref={(el) => { inputRefs.current[i] = el; }}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleDigitChange(i, e.target.value)}
                    onKeyDown={(e) => handleKeyDown(i, e)}
                    className="w-12 h-14 text-center text-2xl font-bold border-2 border-gray-200 rounded-lg
                      focus:ring-2 focus:ring-primary-300 focus:border-primary-400 outline-none transition-all"
                    style={{ transitionDelay: `${i * 0.04}s` }}
                  />
                ))}
              </div>

              <p className="text-center text-xs text-gray-400">El codigo expira en 5 minutos</p>

              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full text-white py-2.5 rounded-lg font-medium disabled:opacity-50"
                style={{ background: 'linear-gradient(90deg, #7F1D1D, #9B1C2E)' }}
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                    </svg>
                    Verificando...
                  </span>
                ) : 'Verificar Codigo'}
              </button>

              <button
                type="button"
                onClick={handleBackToLogin}
                className="w-full text-gray-400 text-sm hover:text-primary-500 transition-colors"
              >
                Volver al inicio de sesion
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
