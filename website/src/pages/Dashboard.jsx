import { useMemo } from 'react'
import { Card, Col, Row, Button, Empty } from 'antd'
import {
  TeamOutlined,
  ClockCircleOutlined,
  LockOutlined,
  CloseCircleOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import { useDriversRealtime } from '../hooks/useDriversRealtime'

const TONES = {
  blue: 'bg-blue-50 text-blue-600',
  amber: 'bg-amber-50 text-amber-600',
  rose: 'bg-rose-50 text-rose-600',
  slate: 'bg-slate-100 text-slate-600',
}

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

function Dashboard() {
  const navigate = useNavigate()
  const { drivers, loading } = useDriversRealtime()

  const stats = useMemo(() => {
    const by = (s) => drivers.filter((d) => (d.status ?? 'active') === s).length
    return {
      total: drivers.length,
      active: by('active'),
      pending: by('pending'),
      inactive: by('inactive'),
      rejected: by('rejected'),
    }
  }, [drivers])

  return (
    <div>
      <PageHeader
        title="Tổng quan"
        subtitle="Tình hình tài khoản tài xế theo thời gian thực"
      />

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            icon={<TeamOutlined />}
            label="Đang hoạt động"
            value={loading ? '—' : stats.active}
            tone="blue"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            icon={<ClockCircleOutlined />}
            label="Chờ duyệt"
            value={loading ? '—' : stats.pending}
            tone="amber"
            onClick={() => navigate('/drivers')}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            icon={<LockOutlined />}
            label="Đã khoá"
            value={loading ? '—' : stats.inactive}
            tone="rose"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            icon={<CloseCircleOutlined />}
            label="Đã từ chối"
            value={loading ? '—' : stats.rejected}
            tone="slate"
          />
        </Col>
      </Row>

      <Card
        className="mt-4"
        title="Hồ sơ cần xử lý"
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
        {stats.pending > 0 ? (
          <p className="m-0 text-slate-600">
            Có <strong className="text-amber-600">{stats.pending}</strong> tài xế
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
