/* eslint-disable react-refresh/only-export-components -- file cấu hình router, không phải component module */
import { lazy } from 'react'
import { createBrowserRouter, Navigate } from 'react-router-dom'
import DashboardLayout from '../layouts/DashboardLayout'
import ProtectedRoute from './ProtectedRoute'
import Login from '../pages/Login'
import NotFound from '../pages/NotFound'

// Tách mỗi trang thành chunk riêng — mở app chỉ tải trang đang cần, không tải
// cả 8 trang một lúc. DashboardLayout bọc <Suspense> lo phần loading.
const Dashboard = lazy(() => import('../pages/Dashboard'))
const Drivers = lazy(() => import('../pages/Drivers'))
const Vehicles = lazy(() => import('../pages/Vehicles'))
const Maintenance = lazy(() => import('../pages/Maintenance'))
const Inspections = lazy(() => import('../pages/Inspections'))
const Incidents = lazy(() => import('../pages/Incidents'))
const Music = lazy(() => import('../pages/Music'))
const Radio = lazy(() => import('../pages/Radio'))
const Assistant = lazy(() => import('../pages/Assistant'))
const Settings = lazy(() => import('../pages/Settings'))
const CostReport = lazy(() => import('../pages/CostReport'))
const DriverReports = lazy(() => import('../pages/DriverReports'))
const Notifications = lazy(() => import('../pages/Notifications'))

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
          { path: 'inspections', element: <Inspections /> },
          { path: 'costs', element: <CostReport /> },
          { path: 'incidents', element: <Incidents /> },
          { path: 'driver-reports', element: <DriverReports /> },
          { path: 'music', element: <Music /> },
          { path: 'notifications', element: <Notifications /> },
          { path: 'radio', element: <Radio /> },
          { path: 'assistant', element: <Assistant /> },
          { path: 'settings', element: <Settings /> },
        ],
      },
    ],
  },
  { path: '*', element: <NotFound /> },
])

export default router
