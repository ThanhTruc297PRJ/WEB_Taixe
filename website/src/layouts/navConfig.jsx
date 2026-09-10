import {
  DashboardOutlined,
  TeamOutlined,
  CarOutlined,
  ToolOutlined,
  WarningOutlined,
  SettingOutlined,
  RobotOutlined,
  CustomerServiceOutlined,
} from '@ant-design/icons'

// Nguồn dữ liệu điều hướng duy nhất — Sidebar và Header cùng đọc từ đây.
export const NAV_SECTIONS = [
  {
    label: 'Vận hành',
    items: [
      { key: '/dashboard', icon: <DashboardOutlined />, label: 'Tổng quan' },
      { key: '/drivers', icon: <TeamOutlined />, label: 'Quản lý tài xế' },
      { key: '/incidents', icon: <WarningOutlined />, label: 'Sự cố' },
    ],
  },
  {
    label: 'Phương tiện',
    items: [
      { key: '/vehicles', icon: <CarOutlined />, label: 'Danh mục xe' },
      { key: '/maintenance', icon: <ToolOutlined />, label: 'Bảo trì xe' },
    ],
  },
  {
    label: 'Khác',
    items: [
      {
        key: '/music',
        icon: <CustomerServiceOutlined />,
        label: 'Quản lý nhạc',
      },
      { key: '/assistant', icon: <RobotOutlined />, label: 'Trợ lý an toàn' },
      { key: '/settings', icon: <SettingOutlined />, label: 'Cài đặt' },
    ],
  },
]

export const NAV_FLAT = NAV_SECTIONS.flatMap((s) => s.items)

export function navTitle(pathname) {
  return NAV_FLAT.find((i) => pathname.startsWith(i.key))?.label ?? ''
}
