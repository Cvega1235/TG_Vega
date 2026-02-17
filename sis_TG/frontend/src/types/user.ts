export interface UserData {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserCreate {
  email: string;
  password: string;
  full_name: string;
  role: string;
}

export interface UserUpdate {
  email?: string;
  full_name?: string;
  role?: string;
  is_active?: boolean;
}
