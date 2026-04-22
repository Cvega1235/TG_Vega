import apiClient from './client';

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
