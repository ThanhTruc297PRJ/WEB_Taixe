import { useState } from 'react'
import { Layout, Badge, Space, Tooltip, Popover, Empty } from 'antd'
import { MenuFoldOutlined, MenuUnfoldOutlined, BellOutlined } from '@ant-design/icons'
import { useLocation, useNavigate } from 'react-router-dom'
import UserProfile from '../components/UserProfile'
import { navTitle } from './navConfig'
import { useAdminNotifications } from '../hooks/useAdminNotifications'
import { NOTIFICATION_SECTIONS as SECTIONS } from '../config/notificationSections'

const { Header: AntHeader } = Layout

// Style inline (không dùng class Tailwind) cho riêng panel này — nội dung
// Popover của AntD render qua Portal và bị CSS-in-JS của AntD đè mất layout
// flex/khoảng cách của Tailwind trong đó (đã tận mắt thấy vỡ layout khi test
// bằng class Tailwind thuần). Style inline có độ ưu tiên cao nhất nên luôn
// hiển thị đúng bất kể thứ tự nạp CSS.
const styles = {
  panel: {
    width: 'min(420px, calc(100vw - 32px))',
    maxHeight: '75vh',
    display: 'flex',
    flexDirection: 'column',

  },
  head: {
    display: 'flex',
    alignItems: 'baseline',
    justifyContent: 'space-between',
    gap: 12,
    padding: '14px 18px 12px',
    borderBottom: '1px solid #e2e8f0',
  },
  title: { fontSize: 16, fontWeight: 700, color: '#0f172a' },
  headMeta: { fontSize: 13, color: '#64748b' },
  body: { overflowY: 'auto', padding: '6px 0 10px' },
  empty: { padding: '28px 0' },
  section: { padding: '10px 10px 4px' },
  sectionHead: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '0 8px 6px',
  },
  sectionIcon: (s) => ({
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: 30,
    height: 30,
    flexShrink: 0,
    borderRadius: 8,
    fontSize: 16,
    color: s.color,
    background: s.bg,
  }),
  sectionLabel: {
    flex: 1,
    minWidth: 0,
    fontSize: 14,
    fontWeight: 600,
    color: '#1e293b',
  },
  countPill: (s) => ({
    marginLeft: 6,
    padding: '1px 8px',
    borderRadius: 999,
    fontSize: 12,
    fontWeight: 600,
    color: s.color,
    background: s.bg,
  }),
  seeAll: {
    flexShrink: 0,
    padding: '2px 4px',
    border: 'none',
    background: 'transparent',
    cursor: 'pointer',
    fontSize: 13,
    color: '#2563eb',
  },
  item: (hover) => ({
    display: 'flex',
    alignItems: 'flex-start',
    gap: 10,
    width: '100%',
    padding: '9px 10px 9px 48px',
    border: 'none',
    borderRadius: 8,
    cursor: 'pointer',
    textAlign: 'left',
    background: hover ? '#f1f5f9' : 'transparent',
    transition: 'background 120ms',
  }),
  itemText: { flex: 1, minWidth: 0 },
  itemTitle: {
    fontSize: 14,
    fontWeight: 500,
    color: '#1e293b',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  itemDesc: {
    marginTop: 2,
    fontSize: 13,
    color: '#64748b',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  newTag: {
    flexShrink: 0,
    marginTop: 2,
    padding: '0 6px',
    borderRadius: 4,
    fontSize: 11,
    fontWeight: 600,
    lineHeight: '18px',
    color: '#fff',
    background: '#ef4444',
  },
}

// Việc gấp lên đầu: sự cố, báo cáo của tài xế, rồi tới việc hành chính.
const URGENCY = [
  'recent_incidents',
  'driver_reports',
  'pending_drivers',
  'maintenance_due',
  'inspections_due',
  'reported_music',
]
const ORDERED_SECTIONS = [...SECTIONS].sort(
  (a, b) => URGENCY.indexOf(a.key) - URGENCY.indexOf(b.key),
)

function itemTitle(item) {
  return (
    item.name ||
    item.title ||
    item.plate_number ||
    item.type_label ||
    item.type ||
    item.vehicle_id ||
    item.id
  )
}

function NotificationItem({ section, item, isNew, onClick }) {
  const [hover, setHover] = useState(false)
  const desc = section.describe(item)
  return (
    <button
      type="button"
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      onFocus={() => setHover(true)}
      onBlur={() => setHover(false)}
      style={styles.item(hover)}
    >
      <span style={styles.itemText}>
        <div style={styles.itemTitle}>{itemTitle(item)}</div>
        {desc && <div style={styles.itemDesc}>{desc}</div>}
      </span>
      {isNew && <span style={styles.newTag}>Mới</span>}
    </button>
  )
}

function NotificationPanel({ data, error, newIds, onNavigate }) {
  const activeSections = ORDERED_SECTIONS.filter((s) => (data[s.key]?.count ?? 0) > 0)
  const hasAny = activeSections.length > 0
  const total = activeSections.reduce((sum, s) => sum + data[s.key].count, 0)

  return (
    <div style={styles.panel}>
      <div style={styles.head}>
        <span style={styles.title}>Việc cần chú ý</span>
        {!error && hasAny && <span style={styles.headMeta}>{total} việc chưa xử lý</span>}
      </div>
      <div style={styles.body}>
        {error && (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <span style={{ color: '#ef4444' }}>Không tải được thông báo — {error}</span>
            }
            style={styles.empty}
          />
        )}
        {!error && !hasAny && (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="Không có việc gì cần xử lý"
            style={styles.empty}
          />
        )}
        {!error &&
          activeSections.map((s) => {
            const section = data[s.key]
            const more = section.count - section.items.length
            return (
              <div key={s.key} style={styles.section}>
                <div style={styles.sectionHead}>
                  <span style={styles.sectionIcon(s)}>{s.icon}</span>
                  <span style={styles.sectionLabel}>
                    {s.label}
                    <span style={styles.countPill(s)}>{section.count}</span>
                  </span>
                  <button
                    type="button"
                    style={styles.seeAll}
                    onClick={() => onNavigate(s.path)}
                  >
                    {more > 0 ? `Xem tất cả (${section.count})` : 'Mở trang'} →
                  </button>
                </div>
                {section.items.map((item) => (
                  <NotificationItem
                    key={item.id}
                    section={s}
                    item={item}
                    isNew={newIds.has(item.id)}
                    onClick={() => onNavigate(s.path)}
                  />
                ))}
              </div>
            )
          })}
      </div>
    </div>
  )
}

function Header({ collapsed, onToggle, wsConnected, notificationsRefreshSignal }) {
  const CollapseIcon = collapsed ? MenuUnfoldOutlined : MenuFoldOutlined
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const { data, error, unseenCount, markSeen, seenIds } = useAdminNotifications(
    notificationsRefreshSignal,
  )
  const [open, setOpen] = useState(false)
  // Chụp danh sách "đã xem" NGAY TRƯỚC khi mở chuông để gắn nhãn "Mới" cho các
  // mục xuất hiện từ lần mở trước (markSeen cập nhật lại ngay khi mở).
  const [newIds, setNewIds] = useState(() => new Set())

  const handleOpenChange = (next) => {
    if (next) {
      const seen = new Set(seenIds)
      const fresh = SECTIONS.flatMap((s) => data[s.key]?.items ?? [])
        .map((item) => item.id)
        .filter((id) => !seen.has(id))
      setNewIds(new Set(fresh))
      markSeen()
    }
    setOpen(next)
  }

  const goTo = (path) => {
    setOpen(false)
    navigate(path)
  }

  return (
    <AntHeader className="sticky top-0 z-10 flex items-center justify-between gap-4 border-b border-slate-200 bg-white px-6">
      <div className="flex items-center gap-4">
        <CollapseIcon
          className="cursor-pointer text-lg text-slate-500 transition-colors hover:text-slate-800"
          onClick={onToggle}
          role="button"
          aria-label="Thu gọn menu"
        />
        <span className="whitespace-nowrap text-base font-semibold text-slate-800">
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
          <span
            className={`hidden items-center gap-1.5 whitespace-nowrap rounded-full px-3 py-1 text-xs font-medium sm:flex ${
              wsConnected ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-100 text-slate-400'
            }`}
          >
            <span
              className={`inline-block h-1.5 w-1.5 rounded-full ${
                wsConnected ? 'bg-emerald-500' : 'bg-slate-300'
              }`}
            />
            Đồng bộ Realtime: {wsConnected ? 'Bật' : 'Mất kết nối'}
          </span>
        </Tooltip>
        <Popover
          trigger="click"
          placement="bottomRight"
          arrow={false}
          styles={{ container: { padding: 0, overflow: 'hidden' } }}
          open={open}
          onOpenChange={handleOpenChange}
          content={
            <NotificationPanel
              data={data}
              error={error}
              newIds={newIds}
              onNavigate={goTo}
            />
          }
        >
          <Badge count={unseenCount} offset={[-4, 6]}>
            <button
              type="button"
              aria-label="Việc cần chú ý"
              className="flex h-10 w-10 cursor-pointer items-center justify-center rounded-full border-0 bg-transparent text-xl text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800"
            >
              <BellOutlined />
            </button>
          </Badge>
        </Popover>
        <UserProfile />
      </Space>
    </AntHeader>
  )
}

export default Header
