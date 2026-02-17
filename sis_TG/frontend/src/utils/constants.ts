export const ROLE_LEVELS: Record<string, number> = {
  superadmin: 4,
  admin: 3,
  analista: 2,
  viewer: 1,
};

export const ROLE_LABELS: Record<string, string> = {
  superadmin: 'Super Admin',
  admin: 'Administrador',
  analista: 'Analista',
  viewer: 'Viewer',
};

export const STATUS_LABELS: Record<string, string> = {
  nuevo: 'Nuevo',
  contactado: 'Contactado',
  interesado: 'Interesado',
  cliente: 'Cliente',
  no_interesado: 'No Interesado',
};

export const STATUS_COLORS: Record<string, string> = {
  nuevo: 'bg-gray-100 text-gray-800',
  contactado: 'bg-blue-100 text-blue-800',
  interesado: 'bg-yellow-100 text-yellow-800',
  cliente: 'bg-green-100 text-green-800',
  no_interesado: 'bg-red-100 text-red-800',
};

export const ZONAS_LA_PAZ = [
  'San Miguel', 'Calacoto', 'Sopocachi', 'Miraflores',
  'Zona Sur', 'Centro', 'Obrajes', 'Achumani', 'Irpavi', 'Cota Cota',
];

export const ALL_STATUSES = ['nuevo', 'contactado', 'interesado', 'cliente', 'no_interesado'];
