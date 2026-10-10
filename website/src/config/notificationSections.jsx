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
// thông báo (Header), trang Thông báo và trang Tổng quan (Dashboard), tránh lặp code/định
// nghĩa lệch nhau giữa 2 nơi hiển thị cùng 1 dữ liệu từ GET /admin/notifications/.
/** Đường dẫn (đã lọc) của cả nhóm — `path` có thể là chuỗi hoặc hàm theo dữ liệu nhóm. */
export const sectionPath = (s, section) =>
  typeof s.path === 'function' ? s.path(section) : s.path

/** Đường dẫn khi bấm 1 dòng trong nhóm. */
export const itemPathOf = (s, item, section) =>
  s.itemPath ? s.itemPath(item) : sectionPath(s, section)

export const NOTIFICATION_SECTIONS = [
  {
    key: 'pending_drivers',
    short: 'Duyệt tài xế',
    timeOf: (item) => item.submitted_at,
    timeLabel: 'Đăng ký lúc',
    color: '#2563eb',
    bg: '#eff6ff',
    label: 'Tài xế chờ duyệt',
    path: '/drivers?status=pending',
    itemPath: () => '/drivers?status=pending',
    icon: <TeamOutlined />,
    describe: (item) =>
      item.email_verified ? 'Đã xác thực email — duyệt được ngay' : 'Chưa xác thực email',
  },
  {
    key: 'maintenance_due',
    short: 'Bảo trì',
    timeOf: (item) => item.scheduled_date,
    timeLabel: 'Ngày hẹn',
    color: '#d97706',
    bg: '#fffbeb',
    label: 'Bảo trì sắp tới hạn',
    path: '/maintenance?status=due',
    itemPath: () => '/maintenance?status=due',
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
    short: 'Đăng kiểm',
    timeOf: (item) => item.old_sticker_expiry,
    timeLabel: 'Tem hết hạn',
    color: '#0d9488',
    bg: '#f0fdfa',
    label: 'Đăng kiểm sắp tới hạn',
    path: '/inspections?status=due',
    itemPath: () => '/inspections?status=due',
    icon: <SafetyCertificateOutlined />,
    describe: (item) =>
      item.old_sticker_expiry
        ? `Tem hết hạn ${dayjs(item.old_sticker_expiry).format('DD/MM/YYYY')}`
        : item.station || '',
  },
  {
    key: 'recent_incidents',
    short: 'Sự cố',
    timeOf: (item) => item.detected_at,
    timeLabel: 'Ghi nhận lúc',
    color: '#dc2626',
    bg: '#fef2f2',
    label: 'Sự cố an toàn gần đây',
    // Sự cố trong 24 giờ qua; bấm 1 dòng mở thẳng chi tiết sự cố đó.
    path: '/incidents?days=1',
    itemPath: (item) => `/incidents?days=1&incident=${item.id}`,
    icon: <WarningOutlined />,
    describe: (item) =>
      item.detected_at ? dayjs(item.detected_at).format('HH:mm DD/MM') : '',
  },
  {
    key: 'driver_reports',
    short: 'Báo cáo tài xế',
    timeOf: (item) => item.created_at,
    timeLabel: 'Gửi lúc',
    color: '#7c3aed',
    bg: '#f5f3ff',
    label: 'Báo cáo từ tài xế',
    path: '/driver-reports?status=new',
    itemPath: () => '/driver-reports?status=new',
    icon: <MessageOutlined />,
    describe: (item) => {
      const when = item.created_at ? dayjs(item.created_at).format('HH:mm DD/MM') : ''
      return [item.note, when].filter(Boolean).join(' · ')
    },
  },
  {
    key: 'awaiting_confirmation',
    short: 'Chờ xác nhận',
    timeOf: (item) => item.submitted_at,
    timeLabel: 'Tài xế gửi lúc',
    color: '#9333ea',
    bg: '#faf5ff',
    label: 'Chờ xác nhận bảo trì / đăng kiểm',
    // Nhóm gồm cả bảo trì lẫn đăng kiểm: chỉ có đăng kiểm thì mở trang Đăng kiểm.
    path: (section) =>
      section?.items?.length && section.items.every((i) => i.kind === 'inspection')
        ? '/inspections?status=awaiting_confirmation'
        : '/maintenance?status=awaiting_confirmation',
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
    short: 'Nhạc bị báo cáo',
    timeOf: () => null,
    timeLabel: '',
    color: '#db2777',
    bg: '#fdf2f8',
    label: 'Bài hát bị báo cáo',
    path: '/music?filter=reported',
    itemPath: () => '/music?filter=reported',
    icon: <CustomerServiceOutlined />,
    describe: (item) => {
      const count = item.report_count || 0
      const artist = item.artist || ''
      const reportText = count > 0 ? `${count} lượt báo cáo` : 'Đã bị báo cáo'
      return artist ? `${artist} · ${reportText}` : reportText
    },
  },
]
