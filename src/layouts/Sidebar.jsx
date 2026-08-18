import { Layout, Menu } from 'antd'
import {
  DashboardOutlined,
  TeamOutlined,
  WarningOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useLocation, useNavigate } from 'react-router-dom'

const { Sider } = Layout

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: 'Tổng quan' },
  { key: '/drivers', icon: <TeamOutlined />, label: 'Quản lý tài xế' },
  { key: '/incidents', icon: <WarningOutlined />, label: 'Sự cố' },
  { key: '/settings', icon: <SettingOutlined />, label: 'Cài đặt' },
]

function Sidebar({ collapsed }) {
  const navigate = useNavigate()
  const location = useLocation()

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
