/**
 * TypeScript type definitions for the application.
 */

export interface User {
  id: number
  email: string
  created_at: string
}

export interface Task {
  id: number
  user_id: number
  title: string
  description: string
  priority: 'high' | 'medium' | 'low'
  is_complete: boolean
  created_at: string
  updated_at: string
}

export interface ApiError {
  detail: string
}

export interface TaskCreate {
  title: string
  description?: string
  priority?: 'high' | 'medium' | 'low'
}

export interface TaskUpdate {
  title?: string
  description?: string
  priority?: 'high' | 'medium' | 'low'
}
