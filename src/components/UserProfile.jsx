import { Avatar, Dropdown } from 'antd'
import {
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/useAuth'

const items = [
  { key: 'profile', icon: <SettingOutlined />, label: 'Thông tin tài khoản' },
  { type: 'divider' },
  { key: 'logout', icon: <LogoutOutlined />, label: 'Đăng xuất', danger: true },
]

function UserProfile() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  const handleClick = async ({ key }) => {
    if (key === 'logout') {
      await logout()
      navigate('/login', { replace: true })
    }
    if (key === 'profile') {
      navigate('/settings')
    }
  }

  return (
    <Dropdown
      menu={{ items, onClick: handleClick }}
      placement="bottomRight"
      trigger={['click']}
    >
      <div className="flex items-center gap-2 cursor-pointer select-none">
        <Avatar icon={<UserOutlined />} />
        <span className="text-sm font-medium hidden sm:inline">
          {user?.email ?? 'Admin'}
        </span>
      </div>
    </Dropdown>
  )
}

export default UserProfile
