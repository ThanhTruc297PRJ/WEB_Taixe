import { Layout, Badge, Space, Tooltip } from 'antd'
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BellOutlined,
} from '@ant-design/icons'
import { useLocation } from 'react-router-dom'
import UserProfile from '../components/UserProfile'
import { navTitle } from './navConfig'

const { Header: AntHeader } = Layout

function Header({ collapsed, onToggle, wsConnected }) {
  const CollapseIcon = collapsed ? MenuUnfoldOutlined : MenuFoldOutlined
  const { pathname } = useLocation()

  return (
    <AntHeader className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-200 bg-white px-6">
      <div className="flex items-center gap-4">
        <CollapseIcon
          className="cursor-pointer text-lg text-slate-500 transition-colors hover:text-slate-800"
          onClick={onToggle}
          role="button"
          aria-label="Thu gọn menu"
        />
        <span className="text-base font-semibold text-slate-800">
          {navTitle(pathname)}
        </span>
      </div>
      <Space size="large" align="center">
        <Tooltip
          title={
            wsConnected
              ? 'Đang nhận cảnh báo realtime'
              : 'Mất kết nối cảnh báo realtime'
          }
        >
          <span className="flex items-center gap-1.5 text-xs text-slate-400">
            <span
              className={`inline-block h-2 w-2 rounded-full ${
                wsConnected ? 'bg-emerald-500' : 'bg-slate-300'
              }`}
            />
            Realtime
          </span>
        </Tooltip>
        <Badge dot>
          <BellOutlined className="cursor-pointer text-lg text-slate-500 transition-colors hover:text-slate-800" />
        </Badge>
        <UserProfile />
      </Space>
    </AntHeader>
  )
}

export default Header
