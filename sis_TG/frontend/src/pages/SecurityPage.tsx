import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getSecurityStats, getAuditLogs, getSecurityAlerts,
  encryptExistingData, getEncryptionStatus,
} from '../api/security';
import type { AuditLog } from '../types/security';

const ACTION_LABELS: Record<string, string> = {
  LOGIN_SUCCESS:          'Login exitoso',
  LOGIN_FAILED:           'Login fallido',
  LOGIN_LOCKED:           'Cuenta bloqueada',
  OTP_VERIFIED:           'OTP verificado',
  OTP_FAILED:             'OTP fallido',
  LOGOUT:                 'Cierre de sesión',
  RESTAURANT_STATUS_CHANGE: 'Cambio de estado',
  DATA_EXPORTED:          'Exportación de datos',
  ML_RUN:                 'Análisis ML',
  SCRAPING_RUN:           'Scraping ejecutado',
  USER_CREATED:           'Usuario creado',
  USER_UPDATED:           'Usuario actualizado',
  USER_DELETED:           'Usuario eliminado',
  ACCOUNT_UNLOCKED:       'Cuenta desbloqueada',
  DATA_ENCRYPTED:         'Datos cifrados',
};

const STATUS_STYLES: Record<string, string> = {
  success: 'bg-green-50 text-green-700',
  failure: 'bg-red-50 text-red-700',
  warning: 'bg-yellow-50 text-yellow-700',
};

const SEVERITY_STYLES: Record<string, string> = {
  high:   'bg-red-100 text-red-800 border-red-300',
  medium: 'bg-yellow-50 text-yellow-800 border-yellow-300',
  low:    'bg-blue-50 text-blue-800 border-blue-300',
};

const ACTION_OPTIONS = [
  '', 'LOGIN_SUCCESS', 'LOGIN_FAILED', 'LOGIN_LOCKED',
  'OTP_VERIFIED', 'OTP_FAILED', 'DATA_EXPORTED',
  'ML_RUN', 'SCRAPING_RUN', 'ACCOUNT_UNLOCKED', 'DATA_ENCRYPTED',
];

export default function SecurityPage() {
  const queryClient = useQueryClient();
  const [filterAction, setFilterAction] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterEmail, setFilterEmail] = useState('');
  const [encryptMsg, setEncryptMsg] = useState('');

  const { data: stats } = useQuery({ queryKey: ['securityStats'], queryFn: getSecurityStats });
  const { data: alerts } = useQuery({ queryKey: ['securityAlerts'], queryFn: getSecurityAlerts });
  const { data: encStatus } = useQuery({ queryKey: ['encryptionStatus'], queryFn: getEncryptionStatus });
  const { data: logs, isLoading } = useQuery({
    queryKey: ['auditLogs', filterAction, filterStatus, filterEmail],
    queryFn: () => getAuditLogs({
      limit: 200,
      action: filterAction || undefined,
      status: filterStatus || undefined,
      user_email: filterEmail || undefined,
    }),
  });

  const encryptMutation = useMutation({
    mutationFn: encryptExistingData,
    onSuccess: (res) => {
      setEncryptMsg(res.message);
      queryClient.invalidateQueries({ queryKey: ['securityStats'] });
    },
    onError: (err: any) => setEncryptMsg(err?.response?.data?.detail || 'Error al cifrar'),
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-800">Seguridad</h2>
        <p className="text-gray-500 mt-1 text-sm">
          Controles preventivos, detectivos y correctivos del sistema
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Registros totales', value: stats?.total_logs ?? '—', color: 'text-primary-600', bg: 'bg-primary-50', icon: '📋' },
          { label: 'Fallos de login hoy', value: stats?.failed_logins_today ?? '—', color: 'text-red-600', bg: 'bg-red-50', icon: '🚫' },
          { label: 'Cuentas bloqueadas', value: stats?.locked_accounts ?? '—', color: 'text-orange-600', bg: 'bg-orange-50', icon: '🔒' },
          { label: 'Alertas activas', value: stats?.active_alerts ?? '—', color: 'text-yellow-700', bg: 'bg-yellow-50', icon: '⚠️' },
        ].map((c, i) => (
          <div key={c.label}
            className={`${c.bg} rounded-xl p-4 shadow-sm card-hover animate-fade-in`}
            style={{ animationDelay: `${i * 0.07}s` }}>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg">{c.icon}</span>
              <p className="text-xs text-gray-500 font-medium">{c.label}</p>
            </div>
            <p className={`text-2xl font-bold ${c.color}`}>{c.value}</p>
          </div>
        ))}
      </div>

      {/* Cifrado + Alertas (2 columnas) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Panel de cifrado */}
        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            🔐 Cifrado de datos sensibles
          </h3>
          <div className={`rounded-lg px-4 py-3 mb-4 border text-sm font-medium ${
            encStatus?.encryption_active
              ? 'bg-green-50 border-green-200 text-green-800'
              : 'bg-yellow-50 border-yellow-300 text-yellow-800'
          }`}>
            {encStatus?.encryption_active ? '✓ ' : '⚠ '}
            {encStatus?.message ?? 'Verificando...'}
          </div>

          <p className="text-xs text-gray-500 mb-3">
            Los campos <strong>teléfono</strong> y <strong>dirección</strong> de restaurantes
            se cifran con AES-128 (Fernet). Los registros importados antes de activar el
            cifrado se pueden cifrar con el botón siguiente.
          </p>

          <div className="space-y-2">
            <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-600 space-y-1">
              <p><span className="font-semibold text-green-700">Preventivo:</span> Datos ilegibles si alguien accede al archivo de BD</p>
              <p><span className="font-semibold text-blue-700">Corrección:</span> Cifrado retroactivo de registros existentes</p>
            </div>
            <button
              onClick={() => encryptMutation.mutate()}
              disabled={encryptMutation.isPending || !encStatus?.encryption_active}
              className="btn-primary w-full py-2 rounded-lg text-sm font-medium text-white disabled:opacity-50"
              style={{ background: 'linear-gradient(90deg,#7F1D1D,#9B1C2E)' }}
            >
              {encryptMutation.isPending ? 'Cifrando...' : 'Cifrar registros existentes'}
            </button>
            {encryptMsg && (
              <p className="text-xs text-center text-green-700 animate-fade-in">{encryptMsg}</p>
            )}
          </div>
        </div>

        {/* Alertas activas */}
        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            ⚠️ Alertas de seguridad activas
          </h3>
          {!alerts || alerts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-gray-400">
              <span className="text-3xl mb-2">✅</span>
              <p className="text-sm">Sin alertas activas</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {alerts.map((alert, i) => (
                <div key={i}
                  className={`rounded-lg p-3 border text-sm ${SEVERITY_STYLES[alert.severity]}`}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold capitalize">
                      {alert.type === 'brute_force' ? '🔴 Fuerza bruta' :
                       alert.type === 'locked_account' ? '🔒 Cuenta bloqueada' : '⚠️ IP sospechosa'}
                    </span>
                    <span className="text-xs font-bold uppercase px-2 py-0.5 rounded-full bg-white/70">
                      {alert.severity}
                    </span>
                  </div>
                  <p className="text-xs">{alert.description}</p>
                  {alert.ip_address && (
                    <p className="text-xs mt-1 opacity-70">IP: {alert.ip_address}</p>
                  )}
                  {alert.user_email && (
                    <p className="text-xs mt-1 opacity-70">Usuario: {alert.user_email}</p>
                  )}
                  <p className="text-xs mt-1 opacity-60">
                    {alert.count} evento(s) · Último: {new Date(alert.last_seen).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Headers de seguridad y Rate Limiting (info) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {[
          {
            icon: '🛡️', title: 'Headers HTTP de seguridad',
            type: 'Preventivo',
            items: ['X-Content-Type-Options: nosniff', 'X-Frame-Options: DENY',
                    'X-XSS-Protection: 1; mode=block', 'Referrer-Policy: strict-origin'],
            color: 'border-primary-200 bg-primary-50',
          },
          {
            icon: '⏱️', title: 'Rate Limiting',
            type: 'Preventivo',
            items: ['Auth endpoints: 10 req/min por IP', 'API general: 120 req/min por IP',
                    'Ventana deslizante de 60 segundos', 'Respuesta 429 con Retry-After'],
            color: 'border-blue-200 bg-blue-50',
          },
          {
            icon: '🔑', title: 'Control de acceso',
            type: 'Preventivo',
            items: ['Autenticación JWT + OTP por email', 'Bloqueo tras 5 intentos fallidos',
                    'Bloqueo por 30 minutos automático', 'Roles: superadmin/admin/analista/viewer'],
            color: 'border-green-200 bg-green-50',
          },
        ].map((panel) => (
          <div key={panel.title} className={`rounded-xl p-4 border ${panel.color}`}>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xl">{panel.icon}</span>
              <div>
                <h4 className="font-semibold text-gray-800 text-sm">{panel.title}</h4>
                <span className="text-xs text-gray-500">{panel.type}</span>
              </div>
            </div>
            <ul className="space-y-1">
              {panel.items.map((item) => (
                <li key={item} className="text-xs text-gray-600 flex items-start gap-1">
                  <span className="text-green-600 mt-0.5 flex-shrink-0">✓</span> {item}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {/* Registro de auditoría */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="p-5 border-b border-gray-100">
          <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
            📋 Registro de auditoría
            <span className="text-xs text-gray-400 font-normal">(Detectivo)</span>
          </h3>
          {/* Filtros */}
          <div className="flex flex-wrap gap-3">
            <select
              value={filterAction}
              onChange={(e) => setFilterAction(e.target.value)}
              className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-300 outline-none"
            >
              <option value="">Todas las acciones</option>
              {ACTION_OPTIONS.filter(Boolean).map((a) => (
                <option key={a} value={a}>{ACTION_LABELS[a] || a}</option>
              ))}
            </select>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-300 outline-none"
            >
              <option value="">Todos los estados</option>
              <option value="success">Exitoso</option>
              <option value="failure">Fallido</option>
              <option value="warning">Advertencia</option>
            </select>
            <input
              type="text"
              placeholder="Filtrar por email..."
              value={filterEmail}
              onChange={(e) => setFilterEmail(e.target.value)}
              className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-300 outline-none"
            />
          </div>
        </div>

        {isLoading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-500 mx-auto" />
          </div>
        ) : (
          <div className="overflow-x-auto max-h-[480px] overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 sticky top-0">
                <tr>
                  <th className="text-left py-3 px-3 sm:px-4 text-gray-500 font-medium">Fecha / Hora</th>
                  <th className="text-left py-3 px-3 sm:px-4 text-gray-500 font-medium">Acción</th>
                  <th className="text-left py-3 px-3 sm:px-4 text-gray-500 font-medium hidden sm:table-cell">Usuario</th>
                  <th className="text-left py-3 px-3 sm:px-4 text-gray-500 font-medium hidden lg:table-cell">IP</th>
                  <th className="text-left py-3 px-3 sm:px-4 text-gray-500 font-medium">Estado</th>
                  <th className="text-left py-3 px-3 sm:px-4 text-gray-500 font-medium hidden md:table-cell">Detalles</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {logs?.length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-gray-400">Sin registros</td>
                  </tr>
                )}
                {logs?.map((log: AuditLog) => (
                  <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                    <td className="py-2.5 px-3 sm:px-4 text-gray-500 text-xs whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="py-2.5 px-3 sm:px-4 text-gray-800 text-xs whitespace-nowrap font-medium">
                      {ACTION_LABELS[log.action] || log.action}
                      <span className="block text-gray-400 sm:hidden">{log.user_email || ''}</span>
                    </td>
                    <td className="py-2.5 px-3 sm:px-4 text-gray-600 text-xs hidden sm:table-cell">
                      {log.user_email || <span className="text-gray-300">—</span>}
                    </td>
                    <td className="py-2.5 px-3 sm:px-4 text-gray-500 text-xs font-mono hidden lg:table-cell">
                      {log.ip_address || '—'}
                    </td>
                    <td className="py-2.5 px-3 sm:px-4">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[log.status]}`}>
                        {log.status === 'success' ? 'Exitoso' :
                         log.status === 'failure' ? 'Fallido' : 'Advertencia'}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 sm:px-4 text-gray-500 text-xs max-w-xs truncate hidden md:table-cell">
                      {log.details || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
