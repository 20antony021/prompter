import axios, { AxiosError } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// Standard API error structure
export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
    field?: string;
  };
}

// Error code to friendly message mapping
const ERROR_MESSAGES: Record<string, string> = {
  VALIDATION_ERROR: 'Please check your input and try again.',
  INVALID_INPUT: 'The provided information is invalid.',
  UNAUTHORIZED: 'Please sign in to continue.',
  FORBIDDEN: 'You do not have permission to perform this action.',
  NOT_FOUND: 'The requested resource was not found.',
  CONFLICT: 'This resource already exists.',
  RATE_LIMIT_EXCEEDED: 'Too many requests. Please try again later.',
  DATABASE_ERROR: 'A database error occurred. Please try again.',
  INTERNAL_ERROR: 'An unexpected error occurred. Please try again.',
  SERVICE_UNAVAILABLE: 'Service is temporarily unavailable. Please try again later.',
};

export const api = axios.create({
  baseURL: `${API_BASE_URL}/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptor
api.interceptors.request.use(async (config) => {
  // Get token from Clerk (skip for now if Clerk not configured)
  if (typeof window !== 'undefined') {
    try {
      const { getToken } = await import('@clerk/nextjs');
      const token = await getToken();
      
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      // Clerk not configured yet, continue without auth
      console.log('Auth not configured, continuing without token');
    }
  }
  
  return config;
});

// Add response interceptor to handle errors consistently
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    // Transform API errors to a consistent format
    if (error.response?.data?.error) {
      const apiError = error.response.data.error;
      
      // Add friendly message if available
      const friendlyMessage = ERROR_MESSAGES[apiError.code] || apiError.message;
      
      return Promise.reject({
        code: apiError.code,
        message: friendlyMessage,
        originalMessage: apiError.message,
        details: apiError.details,
        field: apiError.field,
        status: error.response.status,
      });
    }
    
    // Handle network errors
    if (error.message === 'Network Error') {
      return Promise.reject({
        code: 'NETWORK_ERROR',
        message: 'Unable to connect to the server. Please check your internet connection.',
        status: 0,
      });
    }
    
    // Handle timeout errors
    if (error.code === 'ECONNABORTED') {
      return Promise.reject({
        code: 'TIMEOUT',
        message: 'Request timed out. Please try again.',
        status: 0,
      });
    }
    
    // Fallback for unknown errors
    return Promise.reject({
      code: 'UNKNOWN_ERROR',
      message: 'An unexpected error occurred.',
      status: error.response?.status || 0,
    });
  }
);

// API functions
export const brandsApi = {
  list: (orgId: number) => api.get(`/brands?org_id=${orgId}`),
  get: (id: number) => api.get(`/brands/${id}`),
  create: (data: any) => api.post('/brands', data),
  update: (id: number, data: any) => api.put(`/brands/${id}`, data),
  addCompetitor: (brandId: number, data: any) =>
    api.post(`/brands/${brandId}/competitors`, data),
  listCompetitors: (brandId: number) => api.get(`/brands/${brandId}/competitors`),
};

export const scansApi = {
  list: (brandId: number) => api.get(`/scans?brand_id=${brandId}`),
  get: (id: number) => api.get(`/scans/${id}`),
  create: (data: any) => api.post('/scans', data),
  listMentions: (brandId: number) => api.get(`/scans/mentions?brand_id=${brandId}`),
};

export const pagesApi = {
  list: (brandId: number) => api.get(`/pages?brand_id=${brandId}`),
  get: (id: number) => api.get(`/pages/${id}`),
  create: (data: any) => api.post('/pages', data),
  update: (id: number, data: any) => api.put(`/pages/${id}`, data),
  publish: (id: number, data: any) => api.put(`/pages/${id}/publish`, data),
};

export const analyticsApi = {
  getDashboardStats: (brandId: number) => api.get(`/analytics/dashboard?brand_id=${brandId}`),
};

