import { useEffect, useMemo, useState } from 'react'
import { Card, Col, Row, Button, Empty, Badge } from 'antd'
import {
  TeamOutlined,
  ClockCircleOutlined,
  LockOutlined,
  CloseCircleOutlined,
  ArrowRightOutlined,
  CarOutlined,
  ToolOutlined,
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

function StatCard({ icon, label, value, tone = 'blue', onClick }) {
  return (
    <Card
      hoverable={!!onClick}
      onClick={onClick}
      styles={{ body: { padding: 20 } }}
      className="h-full"
    >
      <div className="flex items-center gap-4">
        <span
          className={`flex h-12 w-12 items-center justify-center rounded-xl text-xl ${TONES[tone]}`}
        >
          {icon}
        </span>
        <div>
          <div className="text-2xl font-bold text-slate-800">{value}</div>
          <div className="text-sm text-slate-500">{label}</div>
        </div>
      </div>
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

function WeeklyIncidentChart({ data }) {
  const max = Math.max(1, ...data.map((d) => d.count))
  const CHART_H = 96

  return (
    <Card className="mt-4" title="Sự cố an toàn theo tuần (8 tuần gần nhất)">
      {data.every((d) => d.count === 0) ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="Chưa có sự cố nào trong 8 tuần gần đây"
        />
      ) : (
        <div className="flex items-end gap-2" style={{ height: CHART_H + 40 }}>
          {data.map((d) => (
            <div
              key={d.label}
              className="flex flex-1 flex-col items-center justify-end gap-1"
              style={{ height: CHART_H + 40 }}
            >
              <div className="text-xs text-slate-500">{d.count > 0 ? d.count : ''}</div>
              <div
                className="w-full max-w-10 rounded-t bg-blue-400"
                style={{ height: Math.max(2, (d.count / max) * CHART_H) }}
              />
              <div className="whitespace-nowrap text-[10px] text-slate-400">{d.label}</div>
            </div>
          ))}
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
    const by = (s) => drivers.filter((d) => (d.status ?? 'active') === s).length
    return {
      total: drivers.length,
      active: by('active'),
      pending: by('pending'),
      inactive: by('inactive'),
      rejected: by('rejected'),
    }
  }, [drivers])

  const vehicleStats = useMemo(() => {
    const by = (s) => vehicles.filter((v) => (v.status ?? 'active') === s).length
    return {
      total: vehicles.length,
      active: by('active'),
      maintenance: by('maintenance'),
      inactive: by('inactive'),
    }
  }, [vehicles])

  const weeklyIncidents = useMemo(() => {
    const now = dayjs()
    const firstWeekStart = now.startOf('week').subtract(WEEKS - 1, 'week')
    const buckets = Array.from({ length: WEEKS }, (_, i) => ({
      label: firstWeekStart.add(i, 'week').format('DD/MM'),
      count: 0,
    }))
    for (const incident of incidents) {
      const d = toDate(incident.detected_at)
      if (!d) continue
      const weekIndex = dayjs(d).startOf('week').diff(firstWeekStart, 'week')
      if (weekIndex >= 0 && weekIndex < WEEKS) buckets[weekIndex].count += 1
    }
    return buckets
  }, [incidents])

  return (
    <div>
      <PageHeader
        title="Tổng quan"
        subtitle="Tình hình đội xe, tài xế và việc cần xử lý theo thời gian thực"
      />

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            icon={<TeamOutlined />}
            label="Đang hoạt động"
            value={loading ? '—' : driverStats.active}
            tone="blue"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            icon={<ClockCircleOutlined />}
            label="Chờ duyệt"
            value={loading ? '—' : driverStats.pending}
            tone="amber"
            onClick={() => navigate('/drivers')}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            icon={<LockOutlined />}
            label="Đã khoá"
            value={loading ? '—' : driverStats.inactive}
            tone="rose"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            icon={<CloseCircleOutlined />}
            label="Đã từ chối"
            value={loading ? '—' : driverStats.rejected}
            tone="slate"
          />
        </Col>
      </Row>

      <Row gutter={[16, 16]} className="mt-4">
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            icon={<CarOutlined />}
            label="Tổng số xe"
            value={vehicleStats.total}
            tone="blue"
            onClick={() => navigate('/vehicles')}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            icon={<CarOutlined />}
            label="Đang chạy"
            value={vehicleStats.active}
            tone="green"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            icon={<ToolOutlined />}
            label="Đang bảo trì"
            value={vehicleStats.maintenance}
            tone="amber"
            onClick={() => navigate('/maintenance')}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            icon={<CloseCircleOutlined />}
            label="Ngừng sử dụng"
            value={vehicleStats.inactive}
            tone="slate"
          />
        </Col>
      </Row>

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

      <WeeklyIncidentChart data={weeklyIncidents} />
    </div>
  )
}

export default Dashboard
