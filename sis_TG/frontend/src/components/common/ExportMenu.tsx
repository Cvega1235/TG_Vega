import { useState } from 'react';
import { exportCSV, exportExcel, exportPDF } from '../../api/exports';

interface Props {
  filters: Record<string, string>;
}

export default function ExportMenu({ filters }: Props) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleExport = async (format: 'csv' | 'excel' | 'pdf') => {
    setLoading(true);
    try {
      if (format === 'csv') await exportCSV(filters);
      else if (format === 'excel') await exportExcel(filters);
      else await exportPDF(filters);
    } catch (err) {
      console.error('Export error:', err);
    } finally {
      setLoading(false);
      setOpen(false);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        disabled={loading}
        className="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 transition-colors disabled:opacity-50"
      >
        {loading ? 'Exportando...' : 'Exportar'}
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-40 bg-white rounded-lg shadow-lg border border-gray-200 z-10">
          <button
            onClick={() => handleExport('csv')}
            className="block w-full text-left px-4 py-2 text-sm hover:bg-gray-50"
          >
            CSV
          </button>
          <button
            onClick={() => handleExport('excel')}
            className="block w-full text-left px-4 py-2 text-sm hover:bg-gray-50"
          >
            Excel (XLSX)
          </button>
          <button
            onClick={() => handleExport('pdf')}
            className="block w-full text-left px-4 py-2 text-sm hover:bg-gray-50"
          >
            PDF
          </button>
        </div>
      )}
    </div>
  );
}
