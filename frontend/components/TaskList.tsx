'use client'

import { Task } from '@/lib/types'

interface TaskListProps {
  tasks: Task[]
  onToggle: (taskId: number) => void
  onRefresh: () => void
}

const priorityColors = {
  high: 'bg-red-100 text-red-800 border-red-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  low: 'bg-green-100 text-green-800 border-green-200'
}

const priorityLabels = {
  high: 'High',
  medium: 'Medium',
  low: 'Low'
}

export default function TaskList({ tasks, onToggle, onRefresh }: TaskListProps) {
  return (
    <div className="bg-white shadow overflow-hidden sm:rounded-md">
      <ul className="divide-y divide-gray-200">
        {tasks.map((task) => (
          <li key={task.id} className="px-6 py-4 hover:bg-gray-50">
            <div className="flex items-start">
              <div className="flex items-center h-5 mt-1">
                <input
                  type="checkbox"
                  checked={task.is_complete}
                  onChange={() => onToggle(task.id)}
                  className="h-5 w-5 text-primary-600 focus:ring-primary-500 border-gray-300 rounded cursor-pointer"
                />
              </div>
              <div className="ml-4 flex-1">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h3
                      className={`text-lg font-medium ${
                        task.is_complete
                          ? 'text-gray-500 line-through'
                          : 'text-gray-900'
                      }`}
                    >
                      {task.title}
                    </h3>
                    {task.description && (
                      <p
                        className={`mt-1 text-sm ${
                          task.is_complete ? 'text-gray-400' : 'text-gray-600'
                        }`}
                      >
                        {task.description}
                      </p>
                    )}
                  </div>
                  <div className="ml-4 flex-shrink-0">
                    <span
                      className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${
                        priorityColors[task.priority]
                      }`}
                    >
                      {priorityLabels[task.priority]}
                    </span>
                  </div>
                </div>
                <div className="mt-2 flex items-center text-xs text-gray-500">
                  <span>Created: {new Date(task.created_at).toLocaleDateString()}</span>
                  {task.updated_at !== task.created_at && (
                    <span className="ml-4">
                      Updated: {new Date(task.updated_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
