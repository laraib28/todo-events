'use client'

import Link from 'next/link'
import { useRouter, usePathname } from 'next/navigation'
import { api } from '@/lib/api'
import { useState } from 'react'

export default function Navbar() {
  const router = useRouter()
  const pathname = usePathname()
  const [loading, setLoading] = useState(false)

  const isAuthenticated = pathname === '/dashboard' || pathname === '/chat'

  const handleLogout = async () => {
    setLoading(true)
    try {
      await api.logout()
      router.push('/login')
    } catch (error) {
      console.error('Logout failed:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <nav className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="text-xl font-bold text-primary-600">
              Todo App
            </Link>
          </div>
          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                <Link
                  href="/dashboard"
                  className={`px-3 py-2 rounded-md text-sm font-medium ${
                    pathname === '/dashboard'
                      ? 'text-primary-600 font-semibold'
                      : 'text-gray-700 hover:text-primary-600'
                  }`}
                >
                  Dashboard
                </Link>
                <Link
                  href="/chat"
                  className={`px-3 py-2 rounded-md text-sm font-medium ${
                    pathname === '/chat'
                      ? 'text-primary-600 font-semibold'
                      : 'text-gray-700 hover:text-primary-600'
                  }`}
                >
                  Chat
                </Link>
                <button
                  onClick={handleLogout}
                  disabled={loading}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50"
                >
                  {loading ? 'Logging out...' : 'Logout'}
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  className="text-gray-700 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Login
                </Link>
                <Link
                  href="/register"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
                >
                  Register
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
