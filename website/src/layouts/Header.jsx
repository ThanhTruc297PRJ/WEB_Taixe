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
  panel: { width: 320, maxHeight: '70vh', overflowY: 'auto' },
  title: { padding: '4px 12px 8px', fontSize: 14, fontWeight: 600, color: '#1e293b' },
  empty: { padding: '16px 0' },
  sectionWrap: { padding: '8px 0', borderTop: '1px solid #f1f5f9' },
  sectionHeader: {
    display: 'flex',
    alignItems: 'center',
    width: '100%',
    padding: '6px 12px',
    background: 'transparent',
    border: 'none',
    cursor: 'pointer',
    textAlign: 'left',
  },
  sectionIcon: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: 22,
    height: 22,
    flexShrink: 0,
    color: '#94a3b8',
    fontSize: 15,
  },
  sectionLabel: {
    flex: 1,
    marginLeft: 8,
    marginRight: 8,
    fontSize: 12,
    fontWeight: 600,
    color: '#475569',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  itemBtn: {
    display: 'block',
    width: '100%',
    padding: '6px 12px 6px 42px',
    background: 'transparent',
    border: 'none',
    cursor: 'pointer',
    textAlign: 'left',
  },
  itemTitle: {
    fontSize: 12,
    fontWeight: 500,
    color: '#334155',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  itemDesc: {
    marginTop: 2,
    fontSize: 11,
    color: '#94a3b8',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
}

function NotificationPanel({ data, error, onNavigate }) {
  const activeSections = SECTIONS.filter((s) => (data[s.key]?.count ?? 0) > 0)
  const hasAny = activeSections.length > 0

  return (
    <div style={styles.panel}>
      <div style={styles.title}>Việc cần chú ý</div>
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
          description="Không có gì cần chú ý"
          style={styles.empty}
        />
      )}
      {!error &&
        hasAny &&
        activeSections.map((s) => {
          const section = data[s.key]
          return (
            <div key={s.key} style={styles.sectionWrap}>
              <button
                type="button"
                onClick={() => onNavigate(s.path)}
                style={styles.sectionHeader}
              >
                <span style={styles.sectionIcon}>{s.icon}</span>
                <span style={styles.sectionLabel}>{s.label}</span>
                <Badge count={section.count} color="#1677ff" />
              </button>
              {section.items.map((item) => {
                const desc = s.describe(item)
                return (
                  <button
                    type="button"
                    key={item.id}
                    onClick={() => onNavigate(s.path)}
                    style={styles.itemBtn}
                  >
                    <div style={styles.itemTitle}>
                      {item.name || item.title || item.type || item.vehicle_id || item.id}
                    </div>
                    {desc && <div style={styles.itemDesc}>{desc}</div>}
                  </button>
                )
              })}
            </div>
          )
        })}
    </div>
  )
}

function Header({ collapsed, onToggle, wsConnected, notificationsRefreshSignal }) {
  const CollapseIcon = collapsed ? MenuUnfoldOutlined : MenuFoldOutlined
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const { data, error, unseenCount, markSeen } = useAdminNotifications(
    notificationsRefreshSignal,
  )

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
          onOpenChange={(open) => {
            if (open) markSeen()
          }}
          content={<NotificationPanel data={data} error={error} onNavigate={navigate} />}
        >
          <Badge count={unseenCount} size="small" offset={[-2, 2]}>
            <BellOutlined className="cursor-pointer text-lg text-slate-500 transition-colors hover:text-slate-800" />
          </Badge>
        </Popover>
        <UserProfile />
      </Space>
    </AntHeader>
  )
}

export default Header
