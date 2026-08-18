import { Layout, Badge, Space } from 'antd'
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BellOutlined,
} from '@ant-design/icons'
import UserProfile from '../components/UserProfile'

const { Header: AntHeader } = Layout

function Header({ collapsed, onToggle }) {
  const CollapseIcon = collapsed ? MenuUnfoldOutlined : MenuFoldOutlined

  return (
    <AntHeader
      style={{ padding: '0 16px', background: '#fff' }}
      className="flex items-center justify-between shadow-sm"
    >
      <CollapseIcon
        className="text-lg cursor-pointer"
        onClick={onToggle}
        role="button"
        aria-label="Toggle sidebar"
      />
      <Space size="large" align="center">
        <Badge dot>
          <BellOutlined className="text-lg cursor-pointer" />
        </Badge>
        <UserProfile />
      </Space>
    </AntHeader>
  )
}

export default Header
