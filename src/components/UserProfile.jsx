import { Avatar, Dropdown } from 'antd'
import {
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const items = [
  { key: 'profile', icon: <SettingOutlined />, label: 'Thông tin tài khoản' },
  { type: 'divider' },
  { key: 'logout', icon: <LogoutOutlined />, label: 'Đăng xuất', danger: true },
]

function UserProfile() {
  const navigate = useNavigate()

  const handleClick = ({ key }) => {
    if (key === 'logout') {
      localStorage.removeItem('admin_token')
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
        <span className="text-sm font-medium hidden sm:inline">Admin</span>
      </div>
    </Dropdown>
  )
}

export default UserProfile
