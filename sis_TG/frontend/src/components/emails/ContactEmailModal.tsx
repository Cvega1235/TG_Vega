import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { sendContactEmail } from '../../api/emails';

interface Props {
  restaurantId: number;
  restaurantName: string;
  onClose: () => void;
}

function buildDefaultBody(restaurantName: string): string {
  return `Estimado equipo de ${restaurantName},

Me pongo en contacto con ustedes de parte de Don Piotr, empresa especializada en productos de charcutería y embutidos de alta calidad.

Hemos identificado su restaurante como un establecimiento con gran potencial para incorporar nuestros productos en su propuesta gastronómica. Nos gustaría presentarles nuestro catálogo y explorar una posible colaboración.

Quedamos a su disposición para concertar una reunión o llamada a su conveniencia.

Atentamente,
Equipo Don Piotr`;
}

export default function ContactEmailModal({ restaurantId, restaurantName, onClose }: Props) {
  const queryClient = useQueryClient();
  const [toEmail, setToEmail] = useState('');
  const [subject, setSubject] = useState(`Don Piotr - Propuesta de Colaboración para ${restaurantName}`);
  const [body, setBody] = useState(buildDefaultBody(restaurantName));
  const [error, setError] = useState('');

  const sendMutation = useMutation({
    mutationFn: () => sendContactEmail({ restaurant_id: restaurantId, to_email: toEmail, subject, body }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes', restaurantId] });
      onClose();
    },
    onError: (err: any) => {
      setError(err?.response?.data?.detail || 'Error al enviar el email. Verifique la configuración SMTP.');
    },
  });

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl flex flex-col max-h-[90vh]">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-800">Enviar Email de Contacto</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Para</label>
            <input
              type="email"
              value={toEmail}
              onChange={(e) => setToEmail(e.target.value)}
              placeholder="email@restaurante.com"
              className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-400 outline-none"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Asunto</label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-400 outline-none"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Mensaje</label>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={12}
              className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-400 outline-none resize-none font-mono"
            />
          </div>

          {error && (
            <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-100">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
          >
            Cancelar
          </button>
          <button
            onClick={() => {
              setError('');
              sendMutation.mutate();
            }}
            disabled={sendMutation.isPending || !toEmail.trim() || !subject.trim() || !body.trim()}
            className="px-5 py-2 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {sendMutation.isPending ? (
              <>
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                Enviando...
              </>
            ) : (
              'Enviar Email'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
