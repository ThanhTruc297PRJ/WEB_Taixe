import { Badge, Layout, Menu } from 'antd'
import { SafetyCertificateFilled } from '@ant-design/icons'
import { useLocation, useNavigate } from 'react-router-dom'
import { useDrivers } from '../contexts/useDrivers'
import { NAV_SECTIONS } from './navConfig'

const { Sider } = Layout

function Sidebar({ collapsed }) {
  const navigate = useNavigate()
  const location = useLocation()
  const { pendingCount } = useDrivers()

  const menuItems = NAV_SECTIONS.map((section) => ({
    key: section.label,
    type: 'group',
    label: collapsed ? '' : section.label.toUpperCase(),
    children: section.items.map((item) => ({
      key: item.key,
      icon: item.icon,
      label:
        item.key === '/drivers' && pendingCount > 0 ? (
          <span className="flex items-center justify-between">
            {item.label}
            <Badge count={pendingCount} size="small" />
          </span>
        ) : (
          item.label
        ),
    })),
  }))

  return (
    <Sider
      trigger={null}
      collapsible
      collapsed={collapsed}
      width={232}
      collapsedWidth={72}
    >
      <div className="flex h-[60px] items-center gap-2.5 px-4 text-white">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-lg">
          <SafetyCertificateFilled />
        </span>
        {!collapsed && (
          <div className="overflow-hidden whitespace-nowrap leading-tight">
            <div className="text-[15px] font-bold">Driver Monitor</div>
            <div className="text-[11px] text-slate-400">Bảng điều khiển</div>
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
        style={{ background: 'transparent', borderInlineEnd: 'none' }}
      />
    </Sider>
  )
}

export default Sidebar
