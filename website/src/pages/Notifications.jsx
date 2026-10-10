import { useCallback, useEffect, useMemo, useState } from 'react'
import { Alert, App, Button, Card, Col, Input, Row, Segmented, Table, Tooltip } from 'antd'
import { ArrowRightOutlined, ReloadOutlined } from '@ant-design/icons'
import { useNavigate, useSearchParams } from 'react-router-dom'
import dayjs from 'dayjs'
import { formatDateTime } from '../utils/datetime'
import PageHeader from '../components/PageHeader'
import { getAdminNotifications } from '../services/adminNotifications'
import {
  NOTIFICATION_SECTIONS,
  itemPathOf,
} from '../config/notificationSections'
import { toDate } from '../utils/firestore'

const POLL_MS = 45_000
const ALL_ITEMS = 500

// Việc gấp lên đầu (giống thứ tự trong chuông thông báo).
const URGENCY = [
  'recent_incidents',
  'driver_reports',
  'awaiting_confirmation',
  'pending_drivers',
  'maintenance_due',
  'inspections_due',
  'reported_music',
]
const SECTIONS = [...NOTIFICATION_SECTIONS].sort(
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

/** Trang Thông báo: toàn bộ việc cần xử lý (không giới hạn 5 mục như chuông),
 * lọc theo loại, tìm kiếm, bấm "Xử lý" để tới đúng chỗ cần làm. */
function Notifications() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const typeFilter = searchParams.get('type') || 'all'
  const setTypeFilter = (value) => setSearchParams(value === 'all' ? {} : { type: value })
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [updatedAt, setUpdatedAt] = useState(null)
  const [search, setSearch] = useState('')

  const load = useCallback(
    async (manual = false) => {
      if (manual) setLoading(true)
      try {
        setData(await getAdminNotifications(ALL_ITEMS))
        setError(null)
        setUpdatedAt(new Date())
        if (manual) message.success('Đã cập nhật')
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    },
    [message],
  )

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- nạp 1 lần + tự làm mới định kỳ
    load()
    const timer = setInterval(() => load(), POLL_MS)
    return () => clearInterval(timer)
  }, [load])

  // Gộp mọi nhóm thành 1 danh sách phẳng.
  const rows = useMemo(() => {
    if (!data) return []
    return SECTIONS.flatMap((s) =>
      (data[s.key]?.items ?? []).map((item) => {
        const when = toDate(s.timeOf(item)) || (s.timeOf(item) ? new Date(s.timeOf(item)) : null)
        return {
          key: `${s.key}:${item.id}`,
          section: s,
          item,
          title: itemTitle(item),
          desc: s.describe(item),
          when,
          path: itemPathOf(s, item, data[s.key]),
        }
      }),
    )
  }, [data])

  const counts = useMemo(() => {
    const c = { all: 0 }
    for (const s of SECTIONS) {
      c[s.key] = data?.[s.key]?.count ?? 0
      c.all += c[s.key]
    }
    return c
  }, [data])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return rows
      .filter((r) => typeFilter === 'all' || r.section.key === typeFilter)
      .filter((r) =>
        !q ? true : [r.title, r.desc].filter(Boolean).some((v) => String(v).toLowerCase().includes(q)),
      )
      .sort((a, b) => {
        const u = URGENCY.indexOf(a.section.key) - URGENCY.indexOf(b.section.key)
        if (u) return u
        return (a.when?.getTime() ?? Infinity) - (b.when?.getTime() ?? Infinity)
      })
  }, [rows, typeFilter, search])

  const columns = [
    {
      title: 'STT',
      key: 'stt',
      width: 55,
      render: (_, __, index) => index + 1,
    },
    {
      title: 'Loại',
      key: 'type',
      width: 200,
      render: (_, r) => (
        <span className="flex items-center gap-2">
          <span
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-base"
            style={{ color: r.section.color, background: r.section.bg }}
          >
            {r.section.icon}
          </span>
          <span className="text-sm font-medium text-slate-700">{r.section.short}</span>
        </span>
      ),
    },
    {
      title: 'Nội dung',
      key: 'content',
      render: (_, r) => (
        <div className="min-w-0 leading-snug">
          <div className="font-medium text-slate-800">{r.title}</div>
          {r.desc && <div className="text-xs text-slate-500">{r.desc}</div>}
        </div>
      ),
    },
    {
      title: 'Thời gian',
      key: 'when',
      width: 170,
      render: (_, r) =>
        r.when ? (
          <div className="leading-snug">
            <div className="text-xs text-slate-400">{r.section.timeLabel}</div>
            <div className="whitespace-nowrap text-sm text-slate-700">
              {['maintenance_due', 'inspections_due'].includes(r.section.key)
                ? dayjs(r.when).format('DD/MM/YYYY')
                : formatDateTime(r.when)}
            </div>
          </div>
        ) : (
          <span className="text-slate-300">—</span>
        ),
    },
    {
      title: '',
      key: 'action',
      width: 120,
      render: (_, r) => (
        <Button
          size="small"
          type="primary"
          ghost
          icon={<ArrowRightOutlined />}
          iconPosition="end"
          onClick={(e) => {
            e.stopPropagation()
            navigate(r.path)
          }}
        >
          Xử lý
        </Button>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="Thông báo"
        subtitle="Toàn bộ việc đang chờ xử lý — xử lý xong việc nào thì việc đó tự biến mất khỏi danh sách"
        extra={
          <Tooltip title={updatedAt ? `Cập nhật lúc ${dayjs(updatedAt).format('HH:mm:ss')}` : ''}>
            <Button icon={<ReloadOutlined />} loading={loading && !!data} onClick={() => load(true)}>
              Làm mới
            </Button>
          </Tooltip>
        }
      />

      {error && (
        <Alert
          className="mb-4"
          type="error"
          showIcon
          message="Không tải được thông báo"
          description={`${error} — kiểm tra máy chủ (backend) đang chạy.`}
        />
      )}

      <Row gutter={[12, 12]} className="mb-4">
        {SECTIONS.map((s) => {
          const active = typeFilter === s.key
          return (
            <Col key={s.key} xs={12} md={8} xl={6} xxl={{ flex: '14.28%' }}>
              <Card
                hoverable
                onClick={() => setTypeFilter(active ? 'all' : s.key)}
                styles={{ body: { padding: 14 } }}
                className="h-full"
                style={active ? { borderColor: s.color, boxShadow: `0 0 0 1px ${s.color}` } : undefined}
              >
                <div className="flex items-center gap-3">
                  <span
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-lg"
                    style={{ color: s.color, background: s.bg }}
                  >
                    {s.icon}
                  </span>
                  <div className="min-w-0">
                    <div className="text-xl font-bold text-slate-800">
                      {data ? counts[s.key] : '—'}
                    </div>
                    <div className="truncate text-xs text-slate-500">{s.short}</div>
                  </div>
                </div>
              </Card>
            </Col>
          )
        })}
      </Row>

      <Card styles={{ body: { padding: 16 } }} className="mb-4">
        <div className="flex flex-wrap items-center gap-3">
          <Input.Search
            allowClear
            placeholder="Tìm theo tên tài xế, biển số, nội dung"
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: 320 }}
          />
          <Segmented
            value={typeFilter}
            onChange={setTypeFilter}
            options={[
              { value: 'all', label: `Tất cả (${counts.all})` },
              ...SECTIONS.filter((s) => counts[s.key] > 0 || typeFilter === s.key).map((s) => ({
                value: s.key,
                label: `${s.short} (${counts[s.key]})`,
              })),
            ]}
          />
        </div>
      </Card>

      <Card styles={{ body: { padding: 0 } }}>
        <Table
          rowKey="key"
          loading={loading && !data}
          columns={columns}
          dataSource={filtered}
          onRow={(r) => ({ onClick: () => navigate(r.path), style: { cursor: 'pointer' } })}
          locale={{
            emptyText:
              typeFilter === 'all' && !search
                ? 'Không có việc gì cần xử lý'
                : 'Không có mục nào khớp bộ lọc',
          }}
          pagination={{ pageSize: 15, showSizeChanger: false, hideOnSinglePage: true }}
          scroll={{ x: 760 }}
        />
      </Card>
    </div>
  )
}

export default Notifications
