import {
  DashboardOutlined,
  TeamOutlined,
  CarOutlined,
  ToolOutlined,
  WarningOutlined,
  SettingOutlined,
  RobotOutlined,
  CustomerServiceOutlined,
  SafetyCertificateOutlined,
  FileTextOutlined,
  MessageOutlined,
  WifiOutlined,
} from '@ant-design/icons'

// Nguồn dữ liệu điều hướng duy nhất — Sidebar và Header cùng đọc từ đây.
export const NAV_SECTIONS = [
  {
    label: 'Vận hành',
    items: [
      { key: '/dashboard', icon: <DashboardOutlined />, label: 'Tổng quan' },
      { key: '/drivers', icon: <TeamOutlined />, label: 'Quản lý tài xế' },
      { key: '/incidents', icon: <WarningOutlined />, label: 'Sự cố an toàn' },
      {
        key: '/driver-reports',
        icon: <MessageOutlined />,
        label: 'Báo cáo từ tài xế',
      },
    ],
  },
  {
    label: 'Phương tiện',
    items: [
      { key: '/vehicles', icon: <CarOutlined />, label: 'Danh mục xe' },
      { key: '/maintenance', icon: <ToolOutlined />, label: 'Bảo trì xe' },
      {
        key: '/inspections',
        icon: <SafetyCertificateOutlined />,
        label: 'Đăng kiểm xe',
      },
      { key: '/costs', icon: <FileTextOutlined />, label: 'Báo cáo chi phí' },
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
      { key: '/radio', icon: <WifiOutlined />, label: 'Quản lý radio' },
      { key: '/assistant', icon: <RobotOutlined />, label: 'Trợ lý AI' },
      { key: '/settings', icon: <SettingOutlined />, label: 'Cài đặt' },
    ],
  },
]

export const NAV_FLAT = NAV_SECTIONS.flatMap((s) => s.items)

export function navTitle(pathname) {
  return NAV_FLAT.find((i) => pathname.startsWith(i.key))?.label ?? ''
}
