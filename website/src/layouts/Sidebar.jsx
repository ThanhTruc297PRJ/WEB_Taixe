import { useEffect, useState } from 'react'
import { Avatar, Badge, Layout, Menu, Tooltip } from 'antd'
import { SafetyCertificateFilled } from '@ant-design/icons'
import { useLocation, useNavigate } from 'react-router-dom'
import { useDrivers } from '../contexts/useDrivers'
import { useAuth } from '../contexts/useAuth'
import { useAdminNotifications } from '../hooks/useAdminNotifications'
import { listVehicles } from '../services/vehicles'
import { initials, avatarColor } from '../utils/avatar'
import { NAV_SECTIONS } from './navConfig'

const { Sider } = Layout

function badgeFor({ key, driversTotal, pendingCount, attention, vehicleCount }) {
  switch (key) {
    case '/drivers':
      return driversTotal > 0
        ? { count: driversTotal, color: pendingCount > 0 ? '#f59e0b' : '#475569' }
        : null
    case '/notifications':
      return attention.total > 0 ? { count: attention.total, color: '#dc2626' } : null
    case '/incidents': {
      const c = attention.recent_incidents.count
      return c > 0 ? { count: c, color: '#dc2626' } : null
    }
    case '/vehicles':
      return vehicleCount > 0 ? { count: vehicleCount, color: '#475569' } : null
    case '/maintenance': {
      const c = attention.maintenance_due.count
      return c > 0 ? { count: c, color: '#f59e0b' } : null
    }
    case '/inspections': {
      const c = attention.inspections_due.count
      return c > 0 ? { count: c, color: '#f59e0b' } : null
    }
    case '/driver-reports': {
      const c = attention.driver_reports.count
      return c > 0 ? { count: c, color: '#f59e0b' } : null
    }
    case '/music': {
      const c = attention.reported_music.count
      return c > 0 ? { count: c, color: '#dc2626' } : null
    }
    default:
      return null
  }
}

function Sidebar({ collapsed }) {
  const navigate = useNavigate()
  const location = useLocation()
  const { drivers, pendingCount } = useDrivers()
  const { user } = useAuth()
  const { data: attention } = useAdminNotifications()
  const [vehicleCount, setVehicleCount] = useState(0)

  useEffect(() => {
    listVehicles()
      .then((v) => setVehicleCount(v.length))
      .catch(() => {
        /* badge số xe chỉ hiện — không chặn sidebar nếu tải lỗi */
      })
  }, [])

  const menuItems = NAV_SECTIONS.map((section) => ({
    key: section.label,
    type: 'group',
    label: collapsed ? '' : section.label.toUpperCase(),
    children: section.items.map((item) => {
      const b = badgeFor({
        key: item.key,
        driversTotal: drivers.length,
        pendingCount,
        attention,
        vehicleCount,
      })
      return {
        key: item.key,
        icon: item.icon,
        label: b ? (
          <span className="flex items-center gap-2">
            {item.label}
            {b.dot ? (
              <span
                className="h-2 w-2 rounded-full"
                style={{ background: b.color }}
              />
            ) : (
              <Badge count={b.count} color={b.color} size="small" />
            )}
          </span>
        ) : (
          item.label
        ),
      }
    }),
  }))

  const displayLabel = user?.displayName || user?.email || 'Admin'

  return (
    <Sider trigger={null} collapsible collapsed={collapsed} width={256} collapsedWidth={72}>
      <div className="flex h-full flex-col">
        <div className="flex h-[60px] shrink-0 items-center gap-2.5 px-4 text-white">
          <span className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-lg">
            <SafetyCertificateFilled />
            <span className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full border-2 border-[#001529] bg-emerald-400" />
          </span>
          {!collapsed && (
            <div className="overflow-hidden whitespace-nowrap leading-tight">
              <div className="text-[15px] font-bold">DriverMonitor</div>
              <div className="text-[10px] tracking-wide text-slate-400">Bảng điều khiển</div>
            </div>
          )}
        </div>
        <div className="mx-3 mb-2 border-t border-white/10" />
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ background: 'transparent', borderInlineEnd: 'none', flex: 1, overflowY: 'auto' }}
        />
      </div>
    </Sider>
  )
}

export default Sidebar
