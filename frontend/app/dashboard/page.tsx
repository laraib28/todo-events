'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { Task } from '@/lib/types'
import Navbar from '@/components/Navbar'
import TaskForm from '@/components/TaskForm'
import TaskList from '@/components/TaskList'

export default function DashboardPage() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)

  const fetchTasks = async () => {
    try {
      setLoading(true)
      const data = await api.getTasks()
      setTasks(data as Task[])
    } catch (err: any) {
      setError(err.message || 'Failed to fetch tasks')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTasks()
  }, [])

  const handleTaskCreated = (newTask: Task) => {
    setTasks([newTask, ...tasks])
    setShowForm(false)
  }

  const handleTaskToggle = async (taskId: number) => {
    try {
      const updatedTask = await api.toggleTask(taskId) as Task
      setTasks(tasks.map(t => t.id === taskId ? updatedTask : t))
    } catch (err: any) {
      setError(err.message || 'Failed to toggle task')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold text-gray-900">My Tasks</h1>
            <button
              onClick={() => setShowForm(!showForm)}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
            >
              {showForm ? 'Cancel' : 'Add Task'}
            </button>
          </div>

          {error && (
            <div className="mb-4 rounded-md bg-red-50 p-4">
              <div className="text-sm text-red-800">{error}</div>
            </div>
          )}

          {showForm && (
            <div className="mb-6">
              <TaskForm onTaskCreated={handleTaskCreated} />
            </div>
          )}

          {loading ? (
            <div className="text-center py-12">
              <div className="text-gray-500">Loading tasks...</div>
            </div>
          ) : tasks.length === 0 ? (
            <div className="text-center py-12">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No tasks yet</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by creating your first task.
              </p>
              {!showForm && (
                <div className="mt-6">
                  <button
                    onClick={() => setShowForm(true)}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
                  >
                    Add Task
                  </button>
                </div>
              )}
            </div>
          ) : (
            <TaskList tasks={tasks} onToggle={handleTaskToggle} onRefresh={fetchTasks} />
          )}
        </div>
      </div>
    </div>
  )
}
