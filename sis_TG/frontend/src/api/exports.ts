import apiClient from './client';

export async function exportCSV(filters: Record<string, string>): Promise<void> {
  const res = await apiClient.get('/exports/csv', { params: filters, responseType: 'blob' });
  downloadBlob(res.data, 'restaurantes_don_piotr.csv', 'text/csv');
}

export async function exportExcel(filters: Record<string, string>): Promise<void> {
  const res = await apiClient.get('/exports/excel', { params: filters, responseType: 'blob' });
  downloadBlob(res.data, 'restaurantes_don_piotr.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
}

export async function exportPDF(filters: Record<string, string>): Promise<void> {
  const res = await apiClient.get('/exports/pdf', { params: filters, responseType: 'blob' });
  downloadBlob(res.data, 'restaurantes_don_piotr.pdf', 'application/pdf');
}

function downloadBlob(data: Blob, filename: string, type: string) {
  const blob = new Blob([data], { type });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  window.URL.revokeObjectURL(url);
}
