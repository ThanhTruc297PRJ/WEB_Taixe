import { Navigate, Outlet } from 'react-router-dom'
import { Spin } from 'antd'
import { useAuth } from '../contexts/useAuth'

function ProtectedRoute() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Spin size="large" />
      </div>
    )
  }

  return user ? <Outlet /> : <Navigate to="/login" replace />
}

export default ProtectedRoute
