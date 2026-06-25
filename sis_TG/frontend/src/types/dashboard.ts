export interface DashboardStats {
  total_restaurants: number;
  avg_rating: number | null;
  high_affinity_count: number;
  clients_count: number;
  in_followup_count: number;
  conversion_rate: number;
  new_clients_this_month: number;
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

export interface RecentSummary {
  days: number;
  new_restaurants: number;
  new_high_score_prospects: number;
  new_clients: number;
  last_scraped_at: string | null;
}

export interface MonthlyKpiPoint {
  month: string;
  label: string;
  new_clients: number;
  lost_clients: number;
  cumulative_clients: number;
  revenue_gained: number;
  revenue_lost: number;
  estimated_revenue: number;
  traffic_clients: 'green' | 'yellow' | 'red';
  traffic_revenue: 'green' | 'yellow' | 'red';
}

export interface KpiEvolutionData {
  monthly: MonthlyKpiPoint[];
  avg_revenue_per_client: number;
  thresholds: Record<string, number>;
  product_details: Array<{
    nombre: string;
    precio_bs_kg: number;
    consumo_kg_mes: number;
    adopcion: number;
    ingreso_esperado_por_cliente: number;
  }>;
  actual_total_revenue: number | null;
  actual_total_clients: number;
}

export interface KpiSettings {
  revenue_green: number;
  revenue_yellow: number;
  clients_green: number;
  clients_yellow: number;
  new_clients_green: number;
  new_clients_yellow: number;
  max_clients: number;
  max_kg_day: number;
}

export interface ClientByMonth {
  id: number;
  nombre: string;
  zona: string | null;
  tipo_cocina: string | null;
  telefono: string | null;
  monthly_revenue: number | null;
  converted_at: string;
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
