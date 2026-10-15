import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  App,
  Button,
  Card,
  Col,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Row,
  Segmented,
  Space,
  Switch,
  Table,
  Tooltip,
} from 'antd'
import {
  PauseCircleFilled,
  PlayCircleFilled,
  PlusOutlined,
  SoundOutlined,
  StopOutlined,
  WifiOutlined,
  CustomerServiceOutlined,
} from '@ant-design/icons'
import { formatDateTime } from '../utils/datetime'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import {
  createStation,
  deleteStation,
  listStations,
  toggleStation,
  updateStation,
} from '../services/radio'

// Khớp với backend (app/models/radio.py): app Android chỉ phát được http://
// ở các domain này, còn lại phải https://.
const CLEARTEXT_HOSTS = ['stream.voh.com.vn']

function validateStreamUrl(_, value) {
  const v = (value || '').trim()
  if (!v) return Promise.reject(new Error('Nhập link phát'))
  let url
  try {
    url = new URL(v)
  } catch {
    return Promise.reject(new Error('Link không hợp lệ'))
  }
  if (url.protocol !== 'http:' && url.protocol !== 'https:') {
    return Promise.reject(new Error('Link phải bắt đầu bằng http:// hoặc https://'))
  }
  if (url.protocol === 'http:' && !CLEARTEXT_HOSTS.includes(url.hostname)) {
    return Promise.reject(
      new Error('Link http:// chỉ hỗ trợ stream.voh.com.vn — kênh khác cần dùng https://'),
    )
  }
  return Promise.resolve()
}

function Radio() {
  const { message } = App.useApp()
  const [form] = Form.useForm()
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(null) // null = đóng, {} = thêm mới, {id..} = sửa
  const [saving, setSaving] = useState(false)
  const [playingId, setPlayingId] = useState(null)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')
  const audioRef = useRef(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      setRows(await listStations())
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

  const hlsRef = useRef(null)

  const stopPreview = useCallback(() => {
    hlsRef.current?.destroy()
    hlsRef.current = null
    const audio = audioRef.current
    if (audio) {
      audio.pause()
      audio.removeAttribute('src')
      audio.load()
    }
    setPlayingId(null)
  }, [])

  useEffect(() => {
    audioRef.current = new Audio()
    return stopPreview
  }, [stopPreview])

  const previewFailed = useCallback(() => {
    stopPreview()
    message.error('Không phát được link này — kiểm tra lại link hoặc đài đang tạm ngừng phát')
  }, [message, stopPreview])

  // Link .m3u8 (HLS): Safari phát thẳng được, Chrome/Edge/Firefox thì cần
  // hls.js (tải riêng khi bấm nghe thử, không làm nặng lúc mở trang).
  const togglePreview = async (station) => {
    const audio = audioRef.current
    if (!audio) return
    const wasPlaying = playingId === station.id
    stopPreview()
    if (wasPlaying) return

    setPlayingId(station.id)
    const url = station.stream_url
    const isHls = /\.m3u8($|\?)/i.test(url)
    try {
      if (isHls && !audio.canPlayType('application/vnd.apple.mpegurl')) {
        const { default: Hls } = await import('hls.js')
        if (!Hls.isSupported()) throw new Error('hls unsupported')
        const hls = new Hls()
        hlsRef.current = hls
        hls.on(Hls.Events.ERROR, (_, data) => {
          if (data.fatal) previewFailed()
        })
        hls.loadSource(url)
        hls.attachMedia(audio)
      } else {
        audio.src = url
      }
      await audio.play()
    } catch {
      previewFailed()
    }
  }

  const stats = useMemo(
    () => ({
      total: rows.length,
      enabled: rows.filter((r) => r.enabled !== false).length,
      disabled: rows.filter((r) => r.enabled === false).length,
      plays: rows.reduce((sum, r) => sum + (r.play_count ?? 0), 0),
    }),
    [rows],
  )

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return rows.filter((r) => {
      if (filter === 'enabled' && r.enabled === false) return false
      if (filter === 'disabled' && r.enabled !== false) return false
      if (!q) return true
      return [r.name, r.frequency].filter(Boolean).some((v) =>
        String(v).toLowerCase().includes(q),
      )
    })
  }, [rows, search, filter])

  const openCreate = () => {
    const nextOrder = rows.reduce((m, r) => Math.max(m, (r.order ?? 0) + 1), 1)
    form.setFieldsValue({
      name: '',
      frequency: '',
      stream_url: '',
      order: nextOrder,
      enabled: true,
    })
    setEditing({})
  }

  const openEdit = (station) => {
    form.setFieldsValue({
      name: station.name,
      frequency: station.frequency ?? '',
      stream_url: station.stream_url,
      order: station.order ?? 0,
      enabled: station.enabled !== false,
    })
    setEditing(station)
  }

  const save = async () => {
    const values = await form.validateFields()
    setSaving(true)
    try {
      if (editing?.id) {
        await updateStation(editing.id, values)
        message.success('Đã lưu kênh')
      } else {
        await createStation(values)
        message.success('Đã thêm kênh')
      }
      setEditing(null)
      load()
    } catch (e) {
      message.error(e.message)
    } finally {
      setSaving(false)
    }
  }

  const onToggle = async (station, enabled) => {
    try {
      await toggleStation(station.id, enabled)
      setRows((prev) =>
        prev.map((r) => (r.id === station.id ? { ...r, enabled } : r)),
      )
      message.success(enabled ? 'Đã bật kênh' : 'Đã tắt kênh')
    } catch (e) {
      message.error(e.message)
    }
  }

  const onDelete = async (station) => {
    try {
      await deleteStation(station.id)
      if (playingId === station.id) stopPreview()
      setRows((prev) => prev.filter((r) => r.id !== station.id))
      message.success('Đã xoá kênh')
    } catch (e) {
      message.error(e.message)
    }
  }

  const columns = [
    {
      title: 'STT',
      key: 'stt',
      width: 55,
      render: (_, __, index) => index + 1,
    },
    {
      title: 'Thứ tự',
      dataIndex: 'order',
      width: 80,
      align: 'center',
      render: (v) => v ?? 0,
    },
    {
      title: 'Kênh',
      dataIndex: 'name',
      render: (name, s) => {
        const isPlaying = playingId === s.id
        return (
          <div className="flex items-center gap-3">
            <Tooltip title={isPlaying ? 'Dừng nghe thử' : 'Nghe thử'}>
              <button
                type="button"
                onClick={() => togglePreview(s)}
                className="shrink-0 text-2xl text-blue-500 transition-colors hover:text-blue-600"
              >
                {isPlaying ? <PauseCircleFilled /> : <PlayCircleFilled />}
              </button>
            </Tooltip>
            <div className="min-w-0 leading-tight">
              <div className="font-medium text-slate-800">{name}</div>
              <div className="text-xs text-slate-400">{s.frequency || '—'}</div>
            </div>
          </div>
        )
      },
    },
    {
      title: 'Link phát',
      dataIndex: 'stream_url',
      ellipsis: { showTitle: false },
      render: (url) => (
        <Tooltip title={url}>
          <span className="font-mono text-xs text-slate-500">{url}</span>
        </Tooltip>
      ),
    },
    {
      title: 'Lượt phát',
      dataIndex: 'play_count',
      width: 100,
      align: 'center',
      render: (v, s) => (
        <Tooltip
          title={
            s.last_played_at
              ? `Lần cuối: ${formatDateTime(s.last_played_at)}`
              : 'Chưa ai nghe'
          }
        >
          {v ?? 0}
        </Tooltip>
      ),
    },
    {
      title: 'Trạng thái',
      dataIndex: 'enabled',
      width: 140,
      render: (enabled, s) => {
        const on = enabled !== false
        return (
          <span className="flex items-center gap-2">
            <Switch checked={on} size="small" onChange={(next) => onToggle(s, next)} />
            <span className={on ? 'text-emerald-600' : 'text-slate-400'}>
              {on ? 'Cho nghe' : 'Đã tắt'}
            </span>
          </span>
        )
      },
    },
    {
      title: '',
      key: 'actions',
      width: 130,
      render: (_, s) => (
        <Space>
          <Button size="small" onClick={() => openEdit(s)}>
            Sửa
          </Button>
          <Popconfirm
            title="Xoá kênh này?"
            description="Tài xế sẽ không thấy kênh này trong app nữa."
            okText="Xoá"
            okButtonProps={{ danger: true }}
            cancelText="Huỷ"
            onConfirm={() => onDelete(s)}
          >
            <Button size="small" danger>
              Xoá
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="Quản lý radio"
        subtitle="Kênh FM tài xế nghe trong app; tắt kênh nào thì tài xế không thấy kênh đó nữa"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            Thêm kênh
          </Button>
        }
      />

      <Row gutter={[16, 16]} className="mb-4">
        <Col xs={12} lg={6} className="flex">
          <StatCard
            icon={<WifiOutlined />}
            label="Tổng kênh"
            value={loading ? '—' : stats.total}
            tone="blue"
          />
        </Col>
        <Col xs={12} lg={6} className="flex">
          <StatCard
            icon={<SoundOutlined />}
            label="Đang cho nghe"
            value={loading ? '—' : stats.enabled}
            tone="green"
          />
        </Col>
        <Col xs={12} lg={6} className="flex">
          <StatCard
            icon={<StopOutlined />}
            label="Đã tắt"
            value={loading ? '—' : stats.disabled}
            tone="rose"
          />
        </Col>
        <Col xs={12} lg={6} className="flex">
          <StatCard
            icon={<CustomerServiceOutlined />}
            label="Tổng lượt phát"
            value={loading ? '—' : stats.plays}
            tone="amber"
          />
        </Col>
      </Row>

      <Card styles={{ body: { padding: 16 } }} className="mb-4">
        <div className="flex flex-wrap items-center gap-3">
          <Input.Search
            allowClear
            placeholder="Tìm theo tên kênh, tần số"
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: 300 }}
          />
          <Segmented
            value={filter}
            onChange={setFilter}
            options={[
              { value: 'all', label: `Tất cả (${stats.total})` },
              { value: 'enabled', label: `Cho nghe (${stats.enabled})` },
              { value: 'disabled', label: `Đã tắt (${stats.disabled})` },
            ]}
          />
        </div>
      </Card>

      <Card styles={{ body: { padding: 0 } }}>
        <Table
          rowKey="id"
          loading={loading}
          columns={columns}
          dataSource={filtered}
          locale={{
            emptyText: rows.length
              ? 'Không có kênh nào khớp bộ lọc'
              : 'Chưa có kênh nào — bấm "Thêm kênh" để tạo',
          }}
          pagination={false}
          scroll={{ x: 760 }}
        />
      </Card>

      <Modal
        open={editing !== null}
        title={editing?.id ? `Sửa kênh: ${editing.name}` : 'Thêm kênh radio'}
        onOk={save}
        onCancel={() => setEditing(null)}
        okText="Lưu"
        cancelText="Huỷ"
        confirmLoading={saving}
        destroyOnHidden
        forceRender
      >
        <Form form={form} layout="vertical" requiredMark={false}>
          <Form.Item
            name="name"
            label="Tên kênh"
            rules={[{ required: true, whitespace: true, message: 'Nhập tên kênh' }]}
          >
            <Input maxLength={80} placeholder="Ví dụ: VOV Giao thông Hà Nội" />
          </Form.Item>
          <Form.Item name="frequency" label="Tần số / mô tả ngắn">
            <Input maxLength={40} placeholder="Ví dụ: FM 91 MHz" />
          </Form.Item>
          <Form.Item
            name="stream_url"
            label="Link phát trực tuyến"
            extra="Link stream của đài (thường đuôi .m3u8, .mp3 hoặc /live). Dùng https://; riêng đài VOH được dùng http://."
            rules={[{ validator: validateStreamUrl }]}
          >
            <Input maxLength={500} placeholder="https://..." />
          </Form.Item>
          <Space size="large" wrap>
            <Form.Item
              name="order"
              label="Thứ tự hiển thị"
              tooltip="Số nhỏ hiện trước trong app"
            >
              <InputNumber min={0} max={999} />
            </Form.Item>
            <Form.Item name="enabled" label="Cho tài xế nghe" valuePropName="checked">
              <Switch />
            </Form.Item>
          </Space>
        </Form>
      </Modal>
    </div>
  )
}

export default Radio
