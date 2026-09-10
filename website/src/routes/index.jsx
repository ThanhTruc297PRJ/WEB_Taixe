import { createBrowserRouter, Navigate } from 'react-router-dom'
import DashboardLayout from '../layouts/DashboardLayout'
import ProtectedRoute from './ProtectedRoute'
import Login from '../pages/Login'
import Dashboard from '../pages/Dashboard'
import Drivers from '../pages/Drivers'
import Vehicles from '../pages/Vehicles'
import Maintenance from '../pages/Maintenance'
import Incidents from '../pages/Incidents'
import Music from '../pages/Music'
import Assistant from '../pages/Assistant'
import Settings from '../pages/Settings'
import NotFound from '../pages/NotFound'

const router = createBrowserRouter([
  { path: '/login', element: <Login /> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <DashboardLayout />,
        children: [
          { index: true, element: <Navigate to="/dashboard" replace /> },
          { path: 'dashboard', element: <Dashboard /> },
          { path: 'drivers', element: <Drivers /> },
          { path: 'vehicles', element: <Vehicles /> },
          { path: 'maintenance', element: <Maintenance /> },
          { path: 'incidents', element: <Incidents /> },
          { path: 'music', element: <Music /> },
          { path: 'assistant', element: <Assistant /> },
          { path: 'settings', element: <Settings /> },
        ],
      },
    ],
  },
  { path: '*', element: <NotFound /> },
])

export default router
