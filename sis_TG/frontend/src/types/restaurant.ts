export interface MLScoreCompact {
  cluster_id: number;
  icp_similarity: number;
  composite_score: number;
}

export interface Restaurant {
  id: number;
  fuente: string;
  url: string | null;
  nombre: string;
  direccion: string | null;
  telefono: string | null;
  rating: number | null;
  num_resenas: number | null;
  latitud: number | null;
  longitud: number | null;
  precio: string | null;
  tipo_cocina: string | null;
  categoria: string | null;
  descripcion: string | null;
  servicios: string | null;
  zona: string | null;
  status: RestaurantStatus;
  monthly_revenue: number | null;
  scraped_at: string | null;
  created_at: string;
  updated_at: string;
  score: ScoreData | null;
  ml_score: MLScoreCompact | null;
}

export type RestaurantStatus = 'nuevo' | 'contactado' | 'interesado' | 'cliente' | 'no_interesado';

export interface ScoreData {
  total_score: number;
  cuisine_score: number | null;
  rating_score: number | null;
  reviews_score: number | null;
  zone_score: number | null;
  price_score: number | null;
  completeness_score: number | null;
  conversion_probability: number | null;
  calculated_at: string;
}

export interface Note {
  id: number;
  restaurant_id: number;
  user_id: string;
  user_name: string | null;
  content: string;
  created_at: string;
}

export interface StatusChange {
  id: number;
  old_status: string | null;
  new_status: string;
  user_name: string | null;
  changed_at: string;
}

export interface PaginatedRestaurants {
  items: Restaurant[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface RestaurantFilters {
  page?: number;
  per_page?: number;
  fuente?: string;
  zona?: string;
  status?: string;
  rating_min?: number;
  rating_max?: number;
  tipo_cocina?: string;
  search?: string;
  sort_by?: string;
  sort_order?: string;
  tiene_embutidos?: boolean;
  min_score?: number;
  prospecto?: boolean;
}
