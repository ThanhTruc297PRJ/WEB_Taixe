import {
  TeamOutlined,
  ToolOutlined,
  SafetyCertificateOutlined,
  WarningOutlined,
  CustomerServiceOutlined,
  MessageOutlined,
  AuditOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'

// Nguồn cấu hình DUY NHẤT cho các loại "việc cần chú ý" — dùng chung bởi chuông
// thông báo (Header) và trang Tổng quan (Dashboard), tránh lặp code/định
// nghĩa lệch nhau giữa 2 nơi hiển thị cùng 1 dữ liệu từ GET /admin/notifications/.
export const NOTIFICATION_SECTIONS = [
  {
    key: 'pending_drivers',
    color: '#2563eb',
    bg: '#eff6ff',
    label: 'Tài xế chờ duyệt',
    path: '/drivers',
    icon: <TeamOutlined />,
    describe: (item) =>
      item.email_verified ? 'Đã xác thực email — duyệt được ngay' : 'Chưa xác thực email',
  },
  {
    key: 'maintenance_due',
    color: '#d97706',
    bg: '#fffbeb',
    label: 'Bảo trì sắp tới hạn',
    path: '/maintenance',
    icon: <ToolOutlined />,
    describe: (item) => {
      const when = item.scheduled_date
        ? `Hẹn ${dayjs(item.scheduled_date).format('DD/MM/YYYY')}`
        : 'Sắp tới hạn theo km'
      return item.type_label ? `${item.type_label} · ${when}` : when
    },
  },
  {
    key: 'inspections_due',
    color: '#0d9488',
    bg: '#f0fdfa',
    label: 'Đăng kiểm sắp tới hạn',
    path: '/inspections',
    icon: <SafetyCertificateOutlined />,
    describe: (item) =>
      item.old_sticker_expiry
        ? `Tem hết hạn ${dayjs(item.old_sticker_expiry).format('DD/MM/YYYY')}`
        : item.station || '',
  },
  {
    key: 'recent_incidents',
    color: '#dc2626',
    bg: '#fef2f2',
    label: 'Sự cố an toàn gần đây',
    path: '/incidents',
    icon: <WarningOutlined />,
    describe: (item) =>
      item.detected_at ? dayjs(item.detected_at).format('HH:mm DD/MM') : '',
  },
  {
    key: 'driver_reports',
    color: '#7c3aed',
    bg: '#f5f3ff',
    label: 'Báo cáo từ tài xế',
    path: '/driver-reports',
    icon: <MessageOutlined />,
    describe: (item) => {
      const when = item.created_at ? dayjs(item.created_at).format('HH:mm DD/MM') : ''
      return [item.note, when].filter(Boolean).join(' · ')
    },
  },
  {
    key: 'awaiting_confirmation',
    color: '#9333ea',
    bg: '#faf5ff',
    label: 'Chờ xác nhận bảo trì / đăng kiểm',
    path: '/maintenance?status=awaiting_confirmation',
    itemPath: (item) =>
      `${item.kind === 'inspection' ? '/inspections' : '/maintenance'}?review=${item.id}`,
    icon: <AuditOutlined />,
    describe: (item) => {
      const when = item.submitted_at ? dayjs(item.submitted_at).format('HH:mm DD/MM') : ''
      return [item.type_label, item.driver_name, when].filter(Boolean).join(' · ')
    },
  },
  {
    key: 'reported_music',
    color: '#db2777',
    bg: '#fdf2f8',
    label: 'Bài hát bị báo cáo',
    path: '/music',
    icon: <CustomerServiceOutlined />,
    describe: (item) => {
      const count = item.report_count || 0
      const artist = item.artist || ''
      const reportText = count > 0 ? `${count} lượt báo cáo` : 'Đã bị báo cáo'
      return artist ? `${artist} · ${reportText}` : reportText
    },
  },
]
