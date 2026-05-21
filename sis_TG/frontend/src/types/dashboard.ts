export interface DashboardStats {
  total_restaurants: number;
  avg_rating: number | null;
  high_affinity_count: number;
  clients_count: number;
  with_embutidos_count: number;
  to_contact_count: number;
  total_with_coordinates: number;
  total_with_phone: number;
  status_counts: Record<string, number>;
  source_counts: Record<string, number>;
}

export interface ChartDataPoint {
  label: string;
  value: number;
}

export interface MapDataPoint {
  id: number;
  nombre: string;
  latitud: number;
  longitud: number;
  rating: number | null;
  status: string;
  total_score: number | null;
  composite_score: number | null;
}

export interface TopScoredItem {
  id: number;
  nombre: string;
  zona: string | null;
  fuente: string;
  rating: number | null;
  status: string;
  total_score: number;
  tipo_cocina: string | null;
  tiene_embutidos: boolean | null;
}

export interface MonthlyConversion {
  month: string;
  label: string;
  count: number;
}

export interface RecentConversion {
  id: number;
  nombre: string;
  zona: string | null;
  tipo_cocina: string | null;
  converted_at: string;
}

export interface ClientHistoryData {
  monthly: MonthlyConversion[];
  recent_conversions: RecentConversion[];
  total_clients: number;
  new_this_month: number;
}

export interface TopProspect {
  id: number;
  nombre: string;
  zona: string | null;
  tipo_cocina: string | null;
  rating: number | null;
  status: string;
  telefono: string | null;
  tiene_embutidos: boolean | null;
  total_score: number;
  cuisine_score: number | null;
  rating_score: number | null;
  reviews_score: number | null;
  zone_score: number | null;
  score_source: 'ml' | 'icp';
}
