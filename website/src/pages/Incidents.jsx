import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  App,
  Button,
  Descriptions,
  Empty,
  Modal,
  Select,
  Space,
  Table,
  Tag,
} from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { listDrivers } from '../services/drivers'
import { listIncidents } from '../services/incidents'

const TYPE_META = {
  drowsiness: { label: 'Buồn ngủ', color: 'gold' },
  distraction: { label: 'Mất tập trung', color: 'blue' },
}

const typeLabel = (t) => TYPE_META[t]?.label ?? t

const MILESTONES = [
  { at: 10, label: 'Nhắc nhở', color: '#faad14' },
  { at: 22, label: 'Cảnh cáo', color: '#fa8c16' },
  { at: 30, label: 'Đình chỉ', color: '#f5222d' },
]

function currentLevel(points) {
  if (points >= 30) return { label: 'Đình chỉ', color: 'red' }
  if (points >= 22) return { label: 'Cảnh cáo', color: 'orange' }
  if (points >= 10) return { label: 'Nhắc nhở', color: 'gold' }
  return { label: 'Bình thường', color: 'green' }
}

function MilestoneBar({ points }) {
  const scale = points > 30 ? points + 5 : 35
  const pct = (v) => `${(v / scale) * 100}%`
  const level = currentLevel(points)

  return (
    <div className="mb-8">
      <div className="flex items-baseline gap-3 mb-1">
        <span className="text-sm text-gray-500">Tổng điểm vi phạm</span>
        <span className="text-2xl font-semibold text-gray-800">{points}</span>
        <Tag color={level.color}>{level.label}</Tag>
      </div>
      <div className="relative h-2.5 rounded-full bg-gray-100 mt-8">
        <div
          className="absolute h-2.5 rounded-full bg-blue-400"
          style={{ width: pct(Math.min(points, scale)) }}
        />
        {MILESTONES.map((m) => (
          <div
            key={m.at}
            className="absolute -top-2"
            style={{ left: pct(m.at) }}
          >
            <div className="h-6 w-0.5" style={{ background: m.color }} />
            <div className="absolute mt-1 -translate-x-1/2 whitespace-nowrap text-xs text-gray-500">
              {m.at} · {m.label}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function IncidentMedia({ incident }) {
  const [imgError, setImgError] = useState(false)

  if (!incident) return null
  const { snapshot_url: snapshot, clip_url: clip } = incident

  if (!snapshot && !clip) {
    return <Empty description="Chưa có hình ảnh / video cho sự cố này" />
  }

  return (
    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
      {snapshot &&
        (imgError ? (
          <Empty description="Không tải được ảnh từ Firebase Storage" />
        ) : (
          <img
            src={snapshot}
            alt="Snapshot lúc vi phạm"
            style={{ width: '100%', borderRadius: 8 }}
            onError={() => setImgError(true)}
          />
        ))}
      {clip && (
        <video
          src={clip}
          controls
          style={{ width: '100%', borderRadius: 8, background: '#000' }}
        />
      )}
    </Space>
  )
}

function Incidents() {
  const { message } = App.useApp()
  const [rows, setRows] = useState([])
  const [drivers, setDrivers] = useState([])
  const [loading, setLoading] = useState(false)
  const [driverFilter, setDriverFilter] = useState('all')
  const [typeFilter, setTypeFilter] = useState('all')
  const [selected, setSelected] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [incidentList, driverList] = await Promise.all([
        listIncidents(),
        listDrivers(),
      ])
      incidentList.sort(
        (a, b) => dayjs(b.detected_at).valueOf() - dayjs(a.detected_at).valueOf(),
      )
      setRows(incidentList)
      setDrivers(driverList)
    } catch (e) {
      message.error(e.message)
    } finally {
      setLoading(false)
    }
  }, [message])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- nạp dữ liệu 1 lần khi mở trang
    load()
  }, [load])

  const driverName = useMemo(() => {
    const map = {}
    for (const d of drivers) map[d.id] = d.name
    return map
  }, [drivers])

  const filtered = useMemo(
    () =>
      rows.filter((r) => {
        if (driverFilter !== 'all' && r.driver_id !== driverFilter) return false
        if (typeFilter !== 'all' && r.type !== typeFilter) return false
        return true
      }),
    [rows, driverFilter, typeFilter],
  )

  const totalPoints = useMemo(
    () => filtered.reduce((sum, r) => sum + (r.points ?? 0), 0),
    [filtered],
  )

  const columns = [
    {
      title: 'Thời gian ghi nhận',
      dataIndex: 'detected_at',
      render: (d) => dayjs(d).format('DD/MM/YYYY HH:mm'),
    },
    {
      title: 'Tài xế',
      dataIndex: 'driver_id',
      render: (id) => driverName[id] || id,
    },
    {
      title: 'Loại',
      dataIndex: 'type',
      render: (t) => <Tag color={TYPE_META[t]?.color}>{typeLabel(t)}</Tag>,
    },
    {
      title: 'Điểm',
      dataIndex: 'points',
      render: (p) => p ?? 0,
    },
    {
      title: 'Độ tin cậy',
      dataIndex: 'confidence',
      render: (c) => (c == null ? '—' : `${Math.round(c * 100)}%`),
    },
    {
      title: '',
      key: 'actions',
      width: 130,
      render: (_, record) => (
        <Button size="small" onClick={() => setSelected(record)}>
          Xem chi tiết
        </Button>
      ),
    },
  ]

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <h1 className="text-xl font-semibold text-gray-800">Báo cáo sự cố</h1>
        <Button icon={<ReloadOutlined />} onClick={load}>
          Làm mới
        </Button>
      </div>

      <MilestoneBar points={totalPoints} />

      <Space className="mb-4" wrap>
        <Select
          value={driverFilter}
          onChange={setDriverFilter}
          style={{ width: 220 }}
          options={[
            { value: 'all', label: 'Tất cả tài xế' },
            ...drivers.map((d) => ({ value: d.id, label: d.name })),
          ]}
        />
        <Select
          value={typeFilter}
          onChange={setTypeFilter}
          style={{ width: 190 }}
          options={[
            { value: 'all', label: 'Tất cả loại' },
            { value: 'drowsiness', label: 'Buồn ngủ' },
            { value: 'distraction', label: 'Mất tập trung' },
          ]}
        />
      </Space>

      <Table
        rowKey="id"
        loading={loading}
        columns={columns}
        dataSource={filtered}
        pagination={{ pageSize: 10, showSizeChanger: false }}
      />

      <Modal
        open={!!selected}
        title="Chi tiết sự cố"
        footer={null}
        onCancel={() => setSelected(null)}
        width={560}
        destroyOnHidden
      >
        {selected && (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <Descriptions column={1} size="small" bordered>
              <Descriptions.Item label="Tài xế">
                {driverName[selected.driver_id] || selected.driver_id}
              </Descriptions.Item>
              <Descriptions.Item label="Loại">
                <Tag color={TYPE_META[selected.type]?.color}>
                  {typeLabel(selected.type)}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Thời gian">
                {dayjs(selected.detected_at).format('DD/MM/YYYY HH:mm:ss')}
              </Descriptions.Item>
              <Descriptions.Item label="Điểm vi phạm">
                {selected.points ?? 0}
              </Descriptions.Item>
              <Descriptions.Item label="Độ tin cậy">
                {selected.confidence == null
                  ? '—'
                  : `${Math.round(selected.confidence * 100)}%`}
              </Descriptions.Item>
              {selected.note && (
                <Descriptions.Item label="Ghi chú">
                  {selected.note}
                </Descriptions.Item>
              )}
            </Descriptions>
            <IncidentMedia incident={selected} />
          </Space>
        )}
      </Modal>
    </div>
  )
}

export default Incidents
