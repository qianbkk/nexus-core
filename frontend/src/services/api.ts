import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type { TokenPair, APIError } from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

class ApiClient {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    this.loadTokens();
    this.setupInterceptors();
  }

  private loadTokens() {
    const storedAccess = localStorage.getItem('access_token');
    const storedRefresh = localStorage.getItem('refresh_token');
    if (storedAccess) this.accessToken = storedAccess;
    if (storedRefresh) this.refreshToken = storedRefresh;
  }

  private saveTokens(tokens: TokenPair) {
    this.accessToken = tokens.access_token;
    this.refreshToken = tokens.refresh_token;
    localStorage.setItem('access_token', tokens.access_token);
    localStorage.setItem('refresh_token', tokens.refresh_token);
  }

  private clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  private setupInterceptors() {
    axios.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        if (this.accessToken && config.headers) {
          config.headers.Authorization = `Bearer ${this.accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    axios.interceptors.response.use(
      (response) => response,
      async (error: AxiosError<APIError>) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
        
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            if (this.refreshToken) {
              const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
                refresh_token: this.refreshToken,
              });
              
              const tokens = response.data as TokenPair;
              this.saveTokens(tokens);
              
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${tokens.access_token}`;
              }
              
              return axios(originalRequest);
            }
          } catch (refreshError) {
            this.clearTokens();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }
        
        return Promise.reject(error);
      }
    );
  }

  setTokens(tokens: TokenPair) {
    this.saveTokens(tokens);
  }

  logout() {
    this.clearTokens();
  }

  getAuthHeaders() {
    return this.accessToken ? { Authorization: `Bearer ${this.accessToken}` } : {};
  }

  async post<T>(url: string, data?: unknown): Promise<T> {
    const response = await axios.post(`${API_BASE_URL}${url}`, data);
    return response.data;
  }

  async get<T>(url: string, params?: Record<string, unknown>): Promise<T> {
    const response = await axios.get(`${API_BASE_URL}${url}`, { params });
    return response.data;
  }

  async put<T>(url: string, data?: unknown): Promise<T> {
    const response = await axios.put(`${API_BASE_URL}${url}`, data);
    return response.data;
  }

  async patch<T>(url: string, data?: unknown): Promise<T> {
    const response = await axios.patch(`${API_BASE_URL}${url}`, data);
    return response.data;
  }

  async delete<T>(url: string): Promise<T> {
    const response = await axios.delete(`${API_BASE_URL}${url}`);
    return response.data;
  }
}

export const api = new ApiClient();
export default api;
