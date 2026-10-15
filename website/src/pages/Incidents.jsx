import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  App,
  Button,
  Card,
  Col,
  Descriptions,
  Empty,
  Image,
  Modal,
  Row,
  Select,
  Space,
  Table,
  Tag,
} from 'antd'
import { PrinterOutlined, ReloadOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { formatDateTime } from '../utils/datetime'
import { collection, onSnapshot } from 'firebase/firestore'
import { db } from '../services/firebase'
import { listIncidents } from '../services/incidents'
import { getSettings } from '../services/settings'
import { useDrivers } from '../contexts/useDrivers'
import { toDate } from '../utils/firestore'
import PageHeader from '../components/PageHeader'
import { PrintableReport, triggerPrint } from '../components/PrintableReport'

const TYPE_META = {
  drowsiness: { label: 'Buồn ngủ', color: 'gold' },
  distraction: { label: 'Mất tập trung', color: 'blue' },
}

const typeLabel = (t) => TYPE_META[t]?.label ?? t

// Mặc định dùng tạm trong lúc chờ tải cấu hình thật từ trang Cài đặt.
const DEFAULT_THRESHOLDS = { reminder: 10, warning: 22, suspend: 30 }

function currentLevel(points, thresholds) {
  if (points >= thresholds.suspend) return { label: 'Đình chỉ', color: 'red' }
  if (points >= thresholds.warning) return { label: 'Cảnh cáo', color: 'orange' }
  if (points >= thresholds.reminder) return { label: 'Nhắc nhở', color: 'gold' }
  return { label: 'Bình thường', color: 'green' }
}

function MilestoneBar({ points, thresholds }) {
  const milestones = [
    { at: thresholds.reminder, label: 'Nhắc nhở', color: '#faad14' },
    { at: thresholds.warning, label: 'Cảnh cáo', color: '#fa8c16' },
    { at: thresholds.suspend, label: 'Đình chỉ', color: '#f5222d' },
  ]
  // Thang chia đều theo mốc (0 → Nhắc nhở → Cảnh cáo → Đình chỉ → cuối thang,
  // mỗi đoạn 25% bề ngang) thay vì tỉ lệ theo điểm: điểm cao (VD 200) không
  // còn dồn 3 mốc về sát mép trái, và nhãn các mốc không bao giờ đè nhau.
  const end = Math.max(points, thresholds.suspend + (thresholds.suspend - thresholds.warning))
  const anchors = [0, thresholds.reminder, thresholds.warning, thresholds.suspend, end]
  const toPercent = (v) => {
    for (let i = 1; i < anchors.length; i += 1) {
      if (v <= anchors[i]) {
        const span = anchors[i] - anchors[i - 1] || 1
        return ((i - 1 + (v - anchors[i - 1]) / span) / (anchors.length - 1)) * 100
      }
    }
    return 100
  }
  const level = currentLevel(points, thresholds)

  return (
    <div className="mb-10">
      <div className="flex items-baseline gap-3 mb-1">
        <span className="text-sm text-gray-500">Tổng điểm vi phạm</span>
        <span className="text-2xl font-semibold text-gray-800">{points}</span>
        <Tag color={level.color}>{level.label}</Tag>
      </div>
      <div className="relative h-2.5 rounded-full bg-gray-100 mt-8">
        <div
          className="absolute h-2.5 rounded-full bg-blue-400"
          style={{ width: `${toPercent(points)}%` }}
        />
        {milestones.map((m) => (
          <div key={m.at} className="absolute -top-2" style={{ left: `${toPercent(m.at)}%` }}>
            <div className="h-6 w-0.5" style={{ background: m.color }} />
            <div className="absolute top-7 -translate-x-1/2 whitespace-nowrap text-xs text-gray-500">
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

const _ts = (v) => {
  const d = toDate(v)
  return d ? d.getTime() : dayjs(v).valueOf() || 0
}

function Incidents() {
  const { message } = App.useApp()
  const { drivers } = useDrivers()
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchParams, setSearchParams] = useSearchParams()
  // Bộ lọc nằm trên đường dẫn (?x=...) để biểu đồ ở trang Tổng quan mở thẳng
  // đúng danh sách đã lọc.
  const setParam = (key, value) =>
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      if (value === undefined || value === null || value === '' || value === 'all')
        next.delete(key)
      else next.set(key, String(value))
      return next
    })
  const driverFilter = searchParams.get('driver') || 'all'
  const typeFilter = searchParams.get('type') || 'all'
  const daysFilter = searchParams.get('days') || 'all'
  const hourParam = searchParams.get('hour')
  const hourFilter = hourParam == null ? null : Number(hourParam)
  const setDriverFilter = (v) => setParam('driver', v)
  const setTypeFilter = (v) => setParam('type', v)
  const setDaysFilter = (v) => setParam('days', v)
  // ?incident=<id> (từ Tổng quan / chuông) mở thẳng chi tiết sự cố đó.
  const [picked, setPicked] = useState(null)
  const incidentParam = searchParams.get('incident')
  const selected =
    picked ?? (incidentParam ? rows.find((r) => r.id === incidentParam) ?? null : null)
  const setSelected = (record) => {
    setPicked(record)
    if (!record && incidentParam) setParam('incident', null)
  }
  const [thresholds, setThresholds] = useState(DEFAULT_THRESHOLDS)

  useEffect(() => {
    getSettings()
      .then((s) => setThresholds(s.violation_thresholds))
      .catch(() => {
        /* giữ mặc định nếu tải cấu hình lỗi — không chặn trang sự cố */
      })
  }, [])

  const applyRows = useCallback((list) => {
    list.sort((a, b) => _ts(b.detected_at) - _ts(a.detected_at))
    setRows(list)
    setLoading(false)
  }, [])

  const reloadOnce = useCallback(async () => {
    setLoading(true)
    try {
      applyRows(await listIncidents())
    } catch (e) {
      message.error(e.message)
      setLoading(false)
    }
  }, [applyRows, message])

  useEffect(() => {
    // Realtime: sự cố mới (do app tài xế gửi) hiện ngay, không cần Làm mới.
    const unsub = onSnapshot(
      collection(db, 'incidents'),
      (snap) => applyRows(snap.docs.map((d) => ({ id: d.id, ...d.data() }))),
      () => {
        // Firestore từ chối (chưa deploy rule 'incidents') -> tải một lần.
        reloadOnce()
      },
    )
    return unsub
  }, [applyRows, reloadOnce])

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
        if (daysFilter !== 'all' || hourFilter != null) {
          const d = toDate(r.detected_at)
          if (!d) return false
          if (daysFilter !== 'all' && !dayjs(d).isAfter(dayjs().subtract(Number(daysFilter), 'day')))
            return false
          if (hourFilter != null && d.getHours() !== hourFilter) return false
        }
        return true
      }),
    [rows, driverFilter, typeFilter, daysFilter, hourFilter],
  )

  const totalPoints = useMemo(
    () => filtered.reduce((sum, r) => sum + (r.points ?? 0), 0),
    [filtered],
  )

  const reportColumns = [
    { key: 'time', label: 'Thời gian', value: (r) => dayjs(toDate(r.detected_at) ?? r.detected_at).format('DD/MM/YYYY HH:mm') },
    { key: 'driver', label: 'Tài xế', value: (r) => driverName[r.driver_id] || r.driver_id },
    { key: 'type', label: 'Loại', value: (r) => typeLabel(r.type) },
    { key: 'points', label: 'Điểm', value: (r) => r.points ?? 0 },
    { key: 'confidence', label: 'Độ tin cậy', value: (r) => (r.confidence == null ? '—' : `${Math.round(r.confidence * 100)}%`) },
  ]

  const columns = [
    {
      title: 'STT',
      key: 'stt',
      width: 55,
      render: (_, __, index) => index + 1,
    },
    {
      title: 'Ảnh tài xế',
      dataIndex: 'photo_url',
      width: 90,
      render: (url) =>
        url ? (
          <Image src={url} width={56} height={56} className="rounded object-cover" />
        ) : (
          <span className="text-slate-300">—</span>
        ),
    },
    {
      title: 'Thời gian ghi nhận',
      dataIndex: 'detected_at',
      width: 170,
      render: (d) => <span className="whitespace-nowrap">{formatDateTime(d)}</span>,
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
      <PageHeader
        title="Báo cáo sự cố"
        subtitle="Lịch sử cảnh báo buồn ngủ, mất tập trung theo tài xế"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={reloadOnce}>
              Làm mới
            </Button>
            <Button
              icon={<PrinterOutlined />}
              onClick={triggerPrint}
              disabled={filtered.length === 0}
            >
              Xuất báo cáo PDF
            </Button>
          </Space>
        }
      />

      <Row gutter={[16, 16]} className="mb-4">
        {[
          {
            key: 'reminder',
            label: 'Mức 1: Nhắc nhở',
            desc: 'Tổng điểm vi phạm của tài xế chạm mốc này',
            color: '#faad14',
            bg: '#fffbe6',
          },
          {
            key: 'warning',
            label: 'Mức 2: Cảnh cáo',
            desc: 'Admin nên chủ động liên hệ nhắc nhở tài xế',
            color: '#fa8c16',
            bg: '#fff7e6',
          },
          {
            key: 'suspend',
            label: 'Mức 3: Đình chỉ tạm thời',
            desc: 'Cân nhắc tạm khoá tài khoản để đảm bảo an toàn',
            color: '#f5222d',
            bg: '#fff1f0',
          },
        ].map((tier) => (
          <Col key={tier.key} xs={24} sm={8}>
            <Card
              styles={{ body: { padding: 16, background: tier.bg } }}
              style={{ borderColor: tier.color, borderWidth: 1 }}
            >
              <div className="text-xs font-semibold" style={{ color: tier.color }}>
                {tier.label.toUpperCase()}
              </div>
              <div className="mt-1 text-2xl font-bold text-slate-800">
                {thresholds[tier.key]} điểm
              </div>
              <div className="mt-1 text-xs text-slate-500">{tier.desc}</div>
            </Card>
          </Col>
        ))}
      </Row>

      <MilestoneBar points={totalPoints} thresholds={thresholds} />

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
        <Select
          value={daysFilter}
          onChange={setDaysFilter}
          style={{ width: 170 }}
          options={[
            { value: 'all', label: 'Mọi thời gian' },
            { value: '7', label: '7 ngày gần nhất' },
            { value: '30', label: '30 ngày gần nhất' },
            { value: '90', label: '90 ngày gần nhất' },
          ]}
        />
        {hourFilter != null && (
          <Tag
            closable
            color="blue"
            onClose={(e) => {
              e.preventDefault()
              setParam('hour', null)
            }}
            style={{ padding: '4px 8px', fontSize: 13 }}
          >
            Khung giờ {String(hourFilter).padStart(2, '0')}:00 –{' '}
            {String(hourFilter).padStart(2, '0')}:59
          </Tag>
        )}
        {searchParams.toString() && (
          <Button type="link" onClick={() => setSearchParams({})}>
            Bỏ lọc
          </Button>
        )}
      </Space>

      <Table
        rowKey="id"
        loading={loading}
        columns={columns}
        dataSource={filtered}
        scroll={{ x: 'max-content' }}
        pagination={{ pageSize: 10, showSizeChanger: false }}
      />

      <PrintableReport
        title="Báo cáo sự cố an toàn"
        subtitle={`Tổng điểm vi phạm: ${totalPoints} · ${filtered.length} sự cố`}
        columns={reportColumns}
        rows={filtered}
      />

      <Modal
        open={!!selected}
        title="Chi tiết sự cố"
        footer={null}
        onCancel={() => setSelected(null)}
        width={560}
        styles={{ body: { maxHeight: '75vh', overflowY: 'auto', paddingRight: 4 } }}
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
                {dayjs(
                  toDate(selected.detected_at) ?? selected.detected_at,
                ).format('DD/MM/YYYY HH:mm:ss')}
              </Descriptions.Item>
              <Descriptions.Item label="Điểm vi phạm">
                {selected.points ?? 0}
              </Descriptions.Item>
              <Descriptions.Item label="Độ tin cậy">
                {selected.confidence == null
                  ? '—'
                  : `${Math.round(selected.confidence * 100)}%`}
              </Descriptions.Item>
              {selected.source && (
                <Descriptions.Item label="Nguồn camera">
                  {selected.source === 'external'
                    ? 'Camera gắn trên xe'
                    : 'Camera điện thoại'}
                </Descriptions.Item>
              )}
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
