import { Badge, Layout, Menu } from 'antd'
import {
  DashboardOutlined,
  TeamOutlined,
  CarOutlined,
  ToolOutlined,
  WarningOutlined,
  SettingOutlined,
  RobotOutlined,
} from '@ant-design/icons'
import { useLocation, useNavigate } from 'react-router-dom'
import { useDriversRealtime } from '../hooks/useDriversRealtime'

const { Sider } = Layout

function Sidebar({ collapsed }) {
  const navigate = useNavigate()
  const location = useLocation()
  const { pendingCount } = useDriversRealtime()

  const menuItems = [
    { key: '/dashboard', icon: <DashboardOutlined />, label: 'Tổng quan' },
    {
      key: '/drivers',
      icon: <TeamOutlined />,
      label: (
        <span className="flex items-center justify-between">
          Quản lý tài xế
          {pendingCount > 0 && (
            <Badge count={pendingCount} size="small" offset={[0, 0]} />
          )}
        </span>
      ),
    },
    { key: '/vehicles', icon: <CarOutlined />, label: 'Danh mục xe' },
    { key: '/maintenance', icon: <ToolOutlined />, label: 'Bảo trì xe' },
    { key: '/incidents', icon: <WarningOutlined />, label: 'Sự cố' },
    { key: '/assistant', icon: <RobotOutlined />, label: 'Trợ lý an toàn' },
    { key: '/settings', icon: <SettingOutlined />, label: 'Cài đặt' },
  ]

  return (
    <Sider
      trigger={null}
      collapsible
      collapsed={collapsed}
      theme="dark"
      width={220}
    >
      <div className="h-16 flex items-center justify-center text-white font-bold text-lg overflow-hidden whitespace-nowrap">
        {collapsed ? 'DM' : 'Driver Monitor'}
      </div>
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={({ key }) => navigate(key)}
      />
    </Sider>
  )
}

export default Sidebar
