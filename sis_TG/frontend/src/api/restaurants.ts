import apiClient from './client';
import type { PaginatedRestaurants, Restaurant, Note, StatusChange, RestaurantFilters } from '../types/restaurant';

export async function getRestaurants(filters: RestaurantFilters): Promise<PaginatedRestaurants> {
  const params = Object.fromEntries(
    Object.entries(filters).filter(([, v]) => v !== undefined && v !== '')
  );
  const res = await apiClient.get<PaginatedRestaurants>('/restaurants', { params });
  return res.data;
}

export async function getRestaurant(id: number): Promise<Restaurant> {
  const res = await apiClient.get<Restaurant>(`/restaurants/${id}`);
  return res.data;
}

export async function updateRestaurantStatus(id: number, status: string): Promise<Restaurant> {
  const res = await apiClient.put<Restaurant>(`/restaurants/${id}/status`, { status });
  return res.data;
}

export async function addNote(restaurantId: number, content: string): Promise<Note> {
  const res = await apiClient.post<Note>(`/restaurants/${restaurantId}/notes`, { content });
  return res.data;
}

export async function getNotes(restaurantId: number): Promise<Note[]> {
  const res = await apiClient.get<Note[]>(`/restaurants/${restaurantId}/notes`);
  return res.data;
}

export async function getHistory(restaurantId: number): Promise<StatusChange[]> {
  const res = await apiClient.get<StatusChange[]>(`/restaurants/${restaurantId}/history`);
  return res.data;
}
