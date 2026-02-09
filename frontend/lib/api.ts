/**
 * API client for backend communication.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api'

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    credentials: 'include',  // Include cookies with every request
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (response.status === 401) {
    // Redirect to login on unauthorized
    if (typeof window !== 'undefined') {
      window.location.href = '/login'
    }
    throw new Error('Unauthorized')
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || 'Request failed')
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T
  }

  return response.json()
}

export const api = {
  // Auth
  register: (email: string, password: string) =>
    apiRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  login: (email: string, password: string) =>
    apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  logout: () => apiRequest('/auth/logout', { method: 'POST' }),

  // Tasks
  getTasks: () => apiRequest('/tasks'),

  createTask: (task: { title: string; description?: string; priority?: string }) =>
    apiRequest('/tasks', {
      method: 'POST',
      body: JSON.stringify(task),
    }),

  updateTask: (id: number, task: { title?: string; description?: string; priority?: string }) =>
    apiRequest(`/tasks/${id}`, {
      method: 'PUT',
      body: JSON.stringify(task),
    }),

  toggleTask: (id: number) =>
    apiRequest(`/tasks/${id}/toggle`, { method: 'PATCH' }),

  deleteTask: (id: number) =>
    apiRequest(`/tasks/${id}`, { method: 'DELETE' }),

  // Chat
  sendChatMessage: (message: string) =>
    apiRequest('/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    }),
}
