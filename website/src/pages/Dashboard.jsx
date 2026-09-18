import { useEffect, useMemo, useState } from 'react'
import { Card, Col, Row, Button, Empty, Badge } from 'antd'
import {
  TeamOutlined,
  CarOutlined,
  WarningOutlined,
  ToolOutlined,
  ArrowRightOutlined,
  RiseOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import PageHeader from '../components/PageHeader'
import { useDrivers } from '../contexts/useDrivers'
import { useAdminNotifications } from '../hooks/useAdminNotifications'
import { NOTIFICATION_SECTIONS } from '../config/notificationSections'
import { listVehicles } from '../services/vehicles'
import { listIncidents } from '../services/incidents'
import { toDate } from '../utils/firestore'

const TONES = {
  blue: 'bg-blue-50 text-blue-600',
  amber: 'bg-amber-50 text-amber-600',
  rose: 'bg-rose-50 text-rose-600',
  slate: 'bg-slate-100 text-slate-600',
  green: 'bg-emerald-50 text-emerald-600',
}

const WEEKS = 8
const PRESENCE_STALE_MS = 120_000
const SPEED_STALE_MS = 30_000

function HeroStatCard({ icon, label, value, trend, tone = 'blue', onClick }) {
  return (
    <Card
      hoverable={!!onClick}
      onClick={onClick}
      styles={{ body: { padding: 20 } }}
      className="h-full"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
          {label}
        </span>
        <span
          className={`flex h-9 w-9 items-center justify-center rounded-lg text-base ${TONES[tone]}`}
        >
          {icon}
        </span>
      </div>
      <div className="mt-2 text-2xl font-bold text-slate-800">{value}</div>
      {trend && (
        <div className="mt-1 flex items-center gap-1 text-xs text-slate-500">
          <RiseOutlined className="text-emerald-500" />
          {trend}
        </div>
      )}
    </Card>
  )
}

function AttentionSection({ data, navigate }) {
  const active = NOTIFICATION_SECTIONS.filter((s) => (data[s.key]?.count ?? 0) > 0)

  return (
    <Card className="mt-4" title="Việc cần chú ý">
      {active.length === 0 ? (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Không có gì cần chú ý" />
      ) : (
        <Row gutter={[16, 16]}>
          {active.map((s) => {
            const section = data[s.key]
            return (
              <Col xs={24} sm={12} lg={8} key={s.key}>
                <div
                  role="button"
                  tabIndex={0}
                  onClick={() => navigate(s.path)}
                  className="h-full cursor-pointer rounded-xl border border-slate-200 p-4 transition-colors hover:border-blue-300 hover:bg-blue-50/40"
                >
                  <div className="mb-2 flex items-center gap-2">
                    <span className="text-lg text-slate-400">{s.icon}</span>
                    <span className="flex-1 text-sm font-semibold text-slate-600">
                      {s.label}
                    </span>
                    <Badge count={section.count} color="#1677ff" />
                  </div>
                  <div className="flex flex-col gap-1">
                    {section.items.slice(0, 3).map((item) => {
                      const title =
                        item.name || item.title || item.type || item.vehicle_id || item.id
                      const desc = s.describe(item)
                      return (
                        <div key={item.id} className="truncate text-xs text-slate-500">
                          {title}
                          {desc ? ` · ${desc}` : ''}
                        </div>
                      )
                    })}
                  </div>
                </div>
              </Col>
            )
          })}
        </Row>
      )}
    </Card>
  )
}

// Đường cong mượt qua các điểm bằng bezier bậc 2 nối tiếp (M..Q..T) — không
// cần thư viện chart, đủ đẹp cho biểu đồ nhỏ trên dashboard.
function smoothPaths(points, height) {
  if (points.length === 0) return { line: '', area: '' }
  if (points.length === 1) {
    const p = points[0]
    return { line: `M${p.x},${p.y}`, area: `M${p.x},${p.y} L${p.x},${height} Z` }
  }
  let line = `M ${points[0].x},${points[0].y}`
  for (let i = 1; i < points.length; i += 1) {
    const p0 = points[i - 1]
    const p1 = points[i]
    const midX = (p0.x + p1.x) / 2
    line += ` Q ${p0.x},${p0.y} ${midX},${(p0.y + p1.y) / 2}`
  }
  const last = points[points.length - 1]
  line += ` T ${last.x},${last.y}`
  const first = points[0]
  const area = `${line} L ${last.x},${height} L ${first.x},${height} Z`
  return { line, area }
}

function WeeklyIncidentChart({ data }) {
  const W = 640
  const H = 160
  const PAD = 8
  const max = Math.max(1, ...data.map((d) => d.drowsiness + d.distraction))
  const step = data.length > 1 ? (W - PAD * 2) / (data.length - 1) : 0
  const yFor = (v) => H - PAD - (v / max) * (H - PAD * 2)

  const drowsyPoints = data.map((d, i) => ({ x: PAD + i * step, y: yFor(d.drowsiness) }))
  const distractPoints = data.map((d, i) => ({ x: PAD + i * step, y: yFor(d.distraction) }))
  const drowsy = smoothPaths(drowsyPoints, H)
  const distract = smoothPaths(distractPoints, H)

  const hasAny = data.some((d) => d.drowsiness + d.distraction > 0)

  return (
    <Card
      className="mt-4"
      title="Sự cố an toàn theo tuần"
      extra={
        <div className="flex items-center gap-4 text-xs text-slate-500">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-red-400" /> Buồn ngủ
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-amber-400" /> Mất tập trung
          </span>
        </div>
      }
    >
      {!hasAny ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="Chưa có sự cố nào trong 8 tuần gần đây"
        />
      ) : (
        <div>
          <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ height: 180 }}>
            <defs>
              <linearGradient id="fillDrowsy" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f87171" stopOpacity="0.35" />
                <stop offset="100%" stopColor="#f87171" stopOpacity="0" />
              </linearGradient>
              <linearGradient id="fillDistract" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#fbbf24" stopOpacity="0" />
              </linearGradient>
            </defs>
            <path d={distract.area} fill="url(#fillDistract)" />
            <path d={drowsy.area} fill="url(#fillDrowsy)" />
            <path d={distract.line} fill="none" stroke="#f59e0b" strokeWidth="2" />
            <path d={drowsy.line} fill="none" stroke="#ef4444" strokeWidth="2" />
          </svg>
          <div className="mt-1 flex justify-between text-[10px] text-slate-400">
            {data.map((d) => (
              <span key={d.label}>{d.label}</span>
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}

function Dashboard() {
  const navigate = useNavigate()
  const { drivers, loading } = useDrivers()
  const { data: attention } = useAdminNotifications()
  const [vehicles, setVehicles] = useState([])
  const [incidents, setIncidents] = useState([])

  useEffect(() => {
    listVehicles()
      .then(setVehicles)
      .catch(() => {
        /* thẻ số liệu xe chỉ hiện — không chặn phần còn lại của dashboard */
      })
    listIncidents()
      .then(setIncidents)
      .catch(() => {
        /* biểu đồ sự cố chỉ hiện rỗng — không chặn phần còn lại của dashboard */
      })
  }, [])

  const driverStats = useMemo(() => {
    const nowMs = dayjs().valueOf()
    const isFresh = (d) => {
      const seen = toDate(d.last_seen)
      return !!seen && nowMs - seen.getTime() <= PRESENCE_STALE_MS
    }
    const online = drivers.filter(
      (d) => (d.presence === 'online' || d.presence === 'driving') && isFresh(d),
    ).length
    const driving = drivers.filter((d) => d.presence === 'driving' && isFresh(d))
    const freshSpeeds = driving
      .map((d) => {
        const updatedAt = toDate(d.speed_updated_at)
        if (d.current_speed_kmh == null || !updatedAt) return null
        if (nowMs - updatedAt.getTime() > SPEED_STALE_MS) return null
        return d.current_speed_kmh
      })
      .filter((v) => v != null)
    const avgSpeed = freshSpeeds.length
      ? Math.round(freshSpeeds.reduce((s, v) => s + v, 0) / freshSpeeds.length)
      : null
    const pending = drivers.filter((d) => (d.status ?? 'active') === 'pending').length
    return {
      total: drivers.length,
      online,
      drivingCount: driving.length,
      avgSpeed,
      pending,
    }
  }, [drivers])

  const todayIncidentStats = useMemo(() => {
    const today = dayjs().startOf('day')
    const todays = incidents.filter((i) => {
      const d = toDate(i.detected_at)
      return d && dayjs(d).isAfter(today)
    })
    const drowsy = todays.filter((i) => i.type === 'drowsiness').length
    const hourCounts = Array(24).fill(0)
    for (const i of todays) {
      const d = toDate(i.detected_at)
      if (d) hourCounts[d.getHours()] += 1
    }
    const peakHour = hourCounts.reduce(
      (best, c, h) => (c > best.c ? { h, c } : best),
      { h: 0, c: 0 },
    )
    return {
      total: todays.length,
      drowsy,
      peakText: peakHour.c > 0 ? `Cao điểm lúc ${peakHour.h}h` : 'Chưa có sự cố hôm nay',
    }
  }, [incidents])

  const maintenanceStats = useMemo(() => {
    const items = [...attention.maintenance_due.items, ...attention.inspections_due.items]
    const dates = items
      .map((i) => toDate(i.scheduled_date) || toDate(i.old_sticker_expiry))
      .filter(Boolean)
      .sort((a, b) => a - b)
    return {
      count: attention.maintenance_due.count + attention.inspections_due.count,
      nearest: dates[0] ? dayjs(dates[0]).format('DD/MM/YYYY') : null,
    }
  }, [attention])

  const weeklyIncidents = useMemo(() => {
    const now = dayjs()
    const firstWeekStart = now.startOf('week').subtract(WEEKS - 1, 'week')
    const buckets = Array.from({ length: WEEKS }, (_, i) => ({
      label: firstWeekStart.add(i, 'week').format('DD/MM'),
      drowsiness: 0,
      distraction: 0,
    }))
    for (const incident of incidents) {
      const d = toDate(incident.detected_at)
      if (!d) continue
      const weekIndex = dayjs(d).startOf('week').diff(firstWeekStart, 'week')
      if (weekIndex < 0 || weekIndex >= WEEKS) continue
      if (incident.type === 'drowsiness') buckets[weekIndex].drowsiness += 1
      else buckets[weekIndex].distraction += 1
    }
    return buckets
  }, [incidents])

  return (
    <div>
      <PageHeader
        title="Tổng quan giám sát đội xe"
        subtitle="Trạng thái hoạt động, chỉ số buồn ngủ và sự cố cần xử lý tức thì."
        extra={
          <div className="flex gap-2">
            <Button icon={<TeamOutlined />} onClick={() => navigate('/drivers')}>
              Xem tài xế
            </Button>
            <Button
              type="primary"
              danger={todayIncidentStats.total > 0}
              icon={<WarningOutlined />}
              onClick={() => navigate('/incidents')}
            >
              Xử lý sự cố {todayIncidentStats.total > 0 ? `(${todayIncidentStats.total})` : ''}
            </Button>
          </div>
        }
      />

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <HeroStatCard
            icon={<TeamOutlined />}
            label="Tài xế trực tuyến"
            value={loading ? '—' : `${driverStats.online} / ${driverStats.total}`}
            trend={
              driverStats.total
                ? `${Math.round((driverStats.online / driverStats.total) * 100)}% đang kết nối app`
                : null
            }
            tone="blue"
            onClick={() => navigate('/drivers')}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <HeroStatCard
            icon={<CarOutlined />}
            label="Xe đang lưu thông"
            value={`${driverStats.drivingCount} / ${vehicles.length || '—'}`}
            trend={
              driverStats.avgSpeed != null
                ? `Tốc độ trung bình ${driverStats.avgSpeed} km/h`
                : 'Chưa có dữ liệu tốc độ'
            }
            tone="green"
            onClick={() => navigate('/vehicles')}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <HeroStatCard
            icon={<WarningOutlined />}
            label="Cảnh báo buồn ngủ"
            value={`${todayIncidentStats.drowsy} vụ hôm nay`}
            trend={todayIncidentStats.peakText}
            tone="rose"
            onClick={() => navigate('/incidents')}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <HeroStatCard
            icon={<ToolOutlined />}
            label="Bảo trì & Đăng kiểm"
            value={`${maintenanceStats.count} xe sắp đến hạn`}
            trend={maintenanceStats.nearest ? `Hạn gần nhất: ${maintenanceStats.nearest}` : null}
            tone="amber"
            onClick={() => navigate('/maintenance')}
          />
        </Col>
      </Row>

      <WeeklyIncidentChart data={weeklyIncidents} />

      <AttentionSection data={attention} navigate={navigate} />

      <Card
        className="mt-4"
        title="Hồ sơ tài xế cần xử lý"
        extra={
          <Button
            type="link"
            onClick={() => navigate('/drivers')}
            icon={<ArrowRightOutlined />}
            iconPosition="end"
          >
            Tới trang quản lý
          </Button>
        }
      >
        {driverStats.pending > 0 ? (
          <p className="m-0 text-slate-600">
            Có <strong className="text-amber-600">{driverStats.pending}</strong> tài xế
            đang chờ bạn duyệt tài khoản.
          </p>
        ) : (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="Không có hồ sơ nào chờ duyệt"
          />
        )}
      </Card>
    </div>
  )
}

export default Dashboard
