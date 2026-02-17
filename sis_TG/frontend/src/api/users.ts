import apiClient from './client';
import type { UserData, UserCreate, UserUpdate } from '../types/user';

export async function getUsers(): Promise<UserData[]> {
  const res = await apiClient.get<UserData[]>('/users');
  return res.data;
}

export async function createUser(data: UserCreate): Promise<UserData> {
  const res = await apiClient.post<UserData>('/users', data);
  return res.data;
}

export async function updateUser(id: string, data: UserUpdate): Promise<UserData> {
  const res = await apiClient.put<UserData>(`/users/${id}`, data);
  return res.data;
}

export async function deleteUser(id: string): Promise<void> {
  await apiClient.delete(`/users/${id}`);
}
