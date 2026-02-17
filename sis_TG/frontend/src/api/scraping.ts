import apiClient from './client';

export interface ScrapingResult {
  message: string;
  source: string;
  total_extracted: number;
  imported: number;
  duplicates: number;
  details: Record<string, unknown>;
}

export async function runScraper(
  source: 'bolivia' | 'gmaps' | 'all' = 'all',
  headless: boolean = true,
  limit?: number,
): Promise<ScrapingResult> {
  const params: Record<string, string | number | boolean> = { source, headless };
  if (limit) params.limit = limit;
  const res = await apiClient.post<ScrapingResult>('/scraping/run', null, { params });
  return res.data;
}
