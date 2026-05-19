import apiClient from './client';

export interface ScrapingRun {
  id: number;
  source_file: string | null;
  source_type: string | null;
  records_total: number | null;
  records_imported: number | null;
  records_skipped: number | null;
  imported_at: string;
}

export interface ScrapingHistory {
  total_restaurants: number;
  runs: ScrapingRun[];
}

export interface ScrapingJob {
  job_id: string;
  status: 'running' | 'completed' | 'error';
  source: string;
  steps_done: number;
  steps_total: number;
  current_step: string;
  total_scraped: number;
  imported: number;
  skipped: number;
  message: string;
  started_at: string;
  finished_at: string | null;
}

export async function runScraper(
  source: 'bolivia' | 'gmaps' | 'all' = 'all',
  headless: boolean = true,
  limit?: number,
): Promise<{ job_id: string; message: string }> {
  const params: Record<string, string | number | boolean> = { source, headless };
  if (limit) params.limit = limit;
  const res = await apiClient.post<{ job_id: string; message: string }>(
    '/scraping/run',
    null,
    { params },
  );
  return res.data;
}

export async function getScrapingStatus(jobId: string): Promise<ScrapingJob> {
  const res = await apiClient.get<ScrapingJob>(`/scraping/status/${jobId}`);
  return res.data;
}

export async function getScrapingHistory(limit = 30): Promise<ScrapingHistory> {
  const res = await apiClient.get<ScrapingHistory>('/scraping/history', { params: { limit } });
  return res.data;
}

// ---------------------------------------------------------------------------
// Enriquecimiento de datos de clientes
// ---------------------------------------------------------------------------

export interface EnrichResult {
  restaurant_id: number;
  restaurant_nombre: string;
  found: boolean;
  updates: Partial<{
    telefono: string;
    latitud: number;
    longitud: number;
    rating: number;
    num_resenas: number;
    tipo_cocina: string;
    website_url: string;
  }>;
}

export interface EnrichJob {
  job_id: string;
  status: 'running' | 'completed' | 'error';
  steps_done: number;
  steps_total: number;
  current_step: string;
  results: EnrichResult[];
  message: string;
  started_at: string;
  finished_at: string | null;
}

export interface EnrichUpdate {
  restaurant_id: number;
  updates: Record<string, unknown>;
}

export async function startEnrichment(headless = true): Promise<{ job_id: string; message: string }> {
  const res = await apiClient.post<{ job_id: string; message: string }>(
    '/scraping/enrich',
    null,
    { params: { headless } },
  );
  return res.data;
}

export async function getEnrichStatus(jobId: string): Promise<EnrichJob> {
  const res = await apiClient.get<EnrichJob>(`/scraping/enrich/status/${jobId}`);
  return res.data;
}

export async function applyEnrichment(updates: EnrichUpdate[]): Promise<{ applied: number }> {
  const res = await apiClient.post<{ applied: number }>('/scraping/enrich/apply', { updates });
  return res.data;
}
