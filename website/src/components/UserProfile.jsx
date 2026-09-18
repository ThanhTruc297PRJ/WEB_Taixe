import { Avatar, Dropdown } from 'antd'
import {
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  DownOutlined,
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
      <div className="flex cursor-pointer select-none items-center gap-2.5 rounded-lg px-2 py-1 transition-colors hover:bg-slate-100">
        <Avatar
          src={user?.photoURL || undefined}
          icon={user?.photoURL ? undefined : <UserOutlined />}
          style={user?.photoURL ? undefined : { backgroundColor: '#2563EB' }}
          size="small"
        />
        <div className="hidden leading-tight sm:block">
          <div className="text-sm font-medium text-slate-800">
            {user?.displayName || user?.email || 'Admin'}
          </div>
          <div className="text-[11px] text-slate-400">Quản trị viên</div>
        </div>
        <DownOutlined className="text-[10px] text-slate-400" />
      </div>
    </Dropdown>
  )
}

export default UserProfile
