import apiClient from './client';

export interface SendContactEmailPayload {
  restaurant_id: number;
  to_email: string;
  subject: string;
  body: string;
}

export async function sendContactEmail(payload: SendContactEmailPayload): Promise<{ success: boolean; message: string }> {
  const res = await apiClient.post('/emails/send-contact', payload);
  return res.data;
}
