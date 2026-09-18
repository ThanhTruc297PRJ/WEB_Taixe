import {
  TeamOutlined,
  ToolOutlined,
  SafetyCertificateOutlined,
  WarningOutlined,
  CustomerServiceOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'

// Nguồn cấu hình DUY NHẤT cho 5 loại "việc cần chú ý" — dùng chung bởi chuông
// thông báo (Header) và trang Tổng quan (Dashboard), tránh lặp code/định
// nghĩa lệch nhau giữa 2 nơi hiển thị cùng 1 dữ liệu từ GET /admin/notifications/.
export const NOTIFICATION_SECTIONS = [
  {
    key: 'pending_drivers',
    label: 'Tài xế chờ duyệt',
    path: '/drivers',
    icon: <TeamOutlined />,
    describe: (item) =>
      item.email_verified ? 'Đã xác thực email — duyệt được ngay' : 'Chưa xác thực email',
  },
  {
    key: 'maintenance_due',
    label: 'Bảo trì sắp tới hạn',
    path: '/maintenance',
    icon: <ToolOutlined />,
    describe: (item) =>
      item.scheduled_date
        ? `Hẹn ${dayjs(item.scheduled_date).format('DD/MM/YYYY')}`
        : 'Sắp tới hạn theo km',
  },
  {
    key: 'inspections_due',
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
    label: 'Sự cố an toàn gần đây',
    path: '/incidents',
    icon: <WarningOutlined />,
    describe: (item) =>
      item.detected_at ? dayjs(item.detected_at).format('HH:mm DD/MM') : '',
  },
  {
    key: 'reported_music',
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
