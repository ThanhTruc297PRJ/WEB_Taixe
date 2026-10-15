import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  App,
  Avatar,
  Badge,
  Button,
  Card,
  Dropdown,
  Form,
  Input,
  Modal,
  Popconfirm,
  Segmented,
  Space,
  Table,
  Tag,
  Tooltip,
  Typography,
} from 'antd'
import { DownOutlined, KeyOutlined, PlusOutlined, SoundOutlined, SyncOutlined } from '@ant-design/icons'
import { useLocation, useSearchParams } from 'react-router-dom'
import dayjs from 'dayjs'
import PageHeader from '../components/PageHeader'
import {
  approveDriver,
  createDriver,
  deleteDriver,
  listDrivers,
  lockDriver,
  rejectDriver,
  resetDriverPassword,
  sendAlertSound,
  unlockDriver,
  updateDriver,
} from '../services/drivers'
import { listVehicles } from '../services/vehicles'
import { listIncidents } from '../services/incidents'
import { getSettings } from '../services/settings'
import { DEFAULT_THRESHOLDS, LEVEL_META, levelOf, levelRange, pointsByDriver } from '../utils/violationLevel'
import { useDrivers } from '../contexts/useDrivers'
import { toDate } from '../utils/firestore'
import { initials, avatarColor } from '../utils/avatar'

const STATUS_META = {
  pending: { label: 'Chờ duyệt', color: 'gold' },
  active: { label: 'Đang hoạt động', color: 'green' },
  inactive: { label: 'Đã khoá', color: 'red' },
  rejected: { label: 'Đã từ chối', color: 'default' },
}

const STALE_MS = 120_000

function presenceInfo(record) {
  const raw = record.presence ?? 'offline'
  const lastSeen = toDate(record.last_seen)
  const stale = !lastSeen || Date.now() - lastSeen.getTime() > STALE_MS
  if (raw === 'driving' && !stale) return { status: 'processing', text: 'Đang lái' }
  if (raw === 'online' && !stale) return { status: 'success', text: 'Trực tuyến' }
  return { status: 'default', text: 'Ngoại tuyến' }
}

// Tốc độ chỉ gửi khi app đang mở ở foreground (không theo dõi nền) — cửa sổ
// "còn mới" ngắn hơn hẳn STALE_MS của presence, vì tài xế tắt/thu nhỏ app là
// dừng gửi ngay, số liệu cũ quá vài chục giây coi như không đáng tin.
const SPEED_STALE_MS = 30_000

function speedText(record) {
  const updatedAt = toDate(record.speed_updated_at)
  if (record.current_speed_kmh == null || !updatedAt) return null
  if (Date.now() - updatedAt.getTime() > SPEED_STALE_MS) return null
  return `${Math.round(record.current_speed_kmh)} km/h`
}

function Drivers() {
  const { message, modal } = App.useApp()
  const location = useLocation()
  const { drivers: liveDrivers, loading, error } = useDrivers()
  const [fallback, setFallback] = useState(null)
  // Điền sẵn từ khoá khi điều hướng tới từ ô tìm nhanh trên Header.
  const [search, setSearch] = useState(location.state?.initialSearch || '')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [saving, setSaving] = useState(false)
  const [rejectTarget, setRejectTarget] = useState(null)
  const [rejectReason, setRejectReason] = useState('')
  const [vehicles, setVehicles] = useState([])
  const [incidents, setIncidents] = useState([])
  const [thresholds, setThresholds] = useState(DEFAULT_THRESHOLDS)
  const [form] = Form.useForm()
  // ?level=suspend… — mở từ biểu đồ "Tài xế theo mức vi phạm" ở Tổng quan.
  const [searchParams, setSearchParams] = useSearchParams()
  const levelFilter = searchParams.get('level')
  const statusFilter = searchParams.get('status') || 'all'
  const setStatusFilter = (value) =>
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      if (value && value !== 'all') next.set('status', value)
      else next.delete('status')
      return next
    })

  useEffect(() => {
    if (!error) return
    message.warning('Không nghe được realtime từ Firestore — dùng dữ liệu tải một lần.')
    listDrivers()
      .then(setFallback)
      .catch((e) => message.error(e.message))
  }, [error, message])

  useEffect(() => {
    listIncidents()
      .then(setIncidents)
      .catch(() => {
        /* cột điểm vi phạm hiện 0 nếu tải sự cố lỗi */
      })
    getSettings()
      .then((s) => s.violation_thresholds && setThresholds(s.violation_thresholds))
      .catch(() => {
        /* giữ ngưỡng mặc định */
      })
  }, [])

  const driverPoints = useMemo(() => pointsByDriver(incidents), [incidents])

  useEffect(() => {
    listVehicles()
      .then(setVehicles)
      .catch(() => {
        /* không chặn trang tài xế nếu tải xe lỗi — cột "Xe phụ trách" chỉ hiện — */
      })
  }, [])

  const vehiclesByDriver = useMemo(() => {
    const map = {}
    for (const v of vehicles) {
      if (!v.driver_id) continue
      ;(map[v.driver_id] ??= []).push(v)
    }
    return map
  }, [vehicles])

  const rows = useMemo(
    () => (error ? (fallback ?? []) : liveDrivers),
    [error, fallback, liveDrivers],
  )

  const counts = useMemo(() => {
    const c = { all: rows.length, pending: 0, active: 0, inactive: 0, rejected: 0 }
    rows.forEach((d) => {
      const s = d.status ?? 'active'
      if (c[s] !== undefined) c[s] += 1
    })
    return c
  }, [rows])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    const result = rows.filter((d) => {
      const status = d.status ?? 'active'
      if (statusFilter !== 'all' && status !== statusFilter) return false
      if (levelFilter) {
        // Giống biểu đồ: chỉ tính tài xế đang hoạt động.
        if (status !== 'active') return false
        if (levelOf(driverPoints[d.id] || 0, thresholds) !== levelFilter) return false
      }
      if (!q) return true
      return [d.name, d.phone, d.license_number, d.email]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(q))
    })
    // Chờ duyệt luôn lên đầu để admin thấy ngay.
    return result.sort((a, b) => {
      const ap = a.status === 'pending' ? 0 : 1
      const bp = b.status === 'pending' ? 0 : 1
      if (ap !== bp) return ap - bp
      return (a.name ?? '').localeCompare(b.name ?? '', 'vi')
    })
  }, [rows, search, statusFilter, levelFilter, driverPoints, thresholds])

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    setModalOpen(true)
  }

  const openEdit = (record) => {
    setEditing(record)
    form.setFieldsValue({
      name: record.name,
      phone: record.phone,
      license_number: record.license_number,
    })
    setModalOpen(true)
  }

  const handleSubmit = async () => {
    let values
    try {
      values = await form.validateFields()
    } catch {
      return
    }
    setSaving(true)
    try {
      if (editing) {
        await updateDriver(editing.id, values)
        message.success('Đã cập nhật tài xế')
      } else {
        await createDriver({ ...values, status: 'active' })
        message.success('Đã thêm tài xế')
      }
      setModalOpen(false)
    } catch (e) {
      message.error(e.message)
    } finally {
      setSaving(false)
    }
  }

  const act = (fn, okMsg) => async (id) => {
    try {
      await fn(id)
      message.success(okMsg)
    } catch (e) {
      message.error(e.message)
    }
  }
  const handleApprove = act(approveDriver, 'Đã duyệt tài khoản')
  const handleLock = act(lockDriver, 'Đã khoá tài khoản')
  const handleUnlock = act(unlockDriver, 'Đã mở khoá')
  const handleDelete = act(deleteDriver, 'Đã xoá')

  const handleResetPassword = (record) => {
    modal.confirm({
      title: `Đặt lại mật khẩu cho ${record.name}?`,
      content:
        'Mật khẩu cũ sẽ ngừng dùng được ngay. Hệ thống tạo mật khẩu tạm mới — ' +
        'bạn cần báo lại cho tài xế ngay sau đó vì chỉ xem được một lần duy nhất.',
      okText: 'Đặt lại',
      cancelText: 'Huỷ',
      onOk: async () => {
        try {
          const { temp_password: tempPassword } = await resetDriverPassword(record.id)
          modal.success({
            title: 'Đã đặt lại mật khẩu',
            content: (
              <div>
                <p className="mb-2 text-sm text-slate-500">
                  Mật khẩu tạm cho <b>{record.name}</b>:
                </p>
                <Typography.Text code copyable style={{ fontSize: 16 }}>
                  {tempPassword}
                </Typography.Text>
                <p className="mt-3 text-xs text-slate-400">
                  Báo ngay cho tài xế — mật khẩu này chỉ hiện một lần, hệ thống không lưu lại.
                </p>
              </div>
            ),
          })
        } catch (e) {
          message.error(e.message)
        }
      },
    })
  }

  const handleAlertSound = async (record) => {
    try {
      const result = await sendAlertSound(record.id)
      if (result.sent) {
        message.success(`Đã gửi cảnh báo tới ${record.name}`)
      } else {
        message.warning(
          result.reason === 'driver_has_no_fcm_token'
            ? `${record.name} chưa mở app trên thiết bị nào để nhận được thông báo`
            : `Không gửi được: ${result.reason}`,
        )
      }
    } catch (e) {
      message.error(e.message)
    }
  }

  const handleReject = async () => {
    const reason = rejectReason.trim()
    if (!reason) {
      message.warning('Nhập lý do từ chối')
      return
    }
    try {
      await rejectDriver(rejectTarget.id, reason)
      message.success('Đã từ chối')
      setRejectTarget(null)
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
      title: 'Tài xế',
      dataIndex: 'name',
      render: (name, record) => (
        <div className="flex items-center gap-3">
          <Avatar
            src={record.photo_url || undefined}
            style={record.photo_url ? undefined : { backgroundColor: avatarColor(record.id || name) }}
          >
            {!record.photo_url && initials(name)}
          </Avatar>
          <div className="leading-tight min-w-0">
            <div className="font-medium text-slate-800">{name || '(chưa có tên)'}</div>
            {record.email && (
              <div className="text-xs text-slate-400 truncate max-w-[180px]">{record.email}</div>
            )}
            <div className="text-xs text-slate-500 mt-0.5 flex flex-wrap gap-x-2">
              {record.phone && <span>{record.phone}</span>}
              {record.license_number && <span className="text-slate-400">{record.license_number}</span>}
            </div>
            {record.status === 'pending' && (
              <Tag
                bordered={false}
                color={record.email_verified ? 'success' : 'default'}
                className="mt-0.5 rounded-full px-2 py-0 text-[11px] leading-4"
              >
                {record.email_verified ? 'Đã xác thực email' : 'Chưa xác thực email'}
              </Tag>
            )}
          </div>
        </div>
      ),
    },
    {
      title: 'Xe phụ trách',
      key: 'vehicles',
      render: (_, record) => {
        const list = vehiclesByDriver[record.id] || []
        if (!list.length) return <span className="text-slate-300">—</span>
        const label = list.length === 1 ? list[0].plate_number : `${list.length} xe`
        return (
          <Tooltip title={list.map((v) => v.plate_number).join(', ')}>
            <Tag bordered={false} color="blue" className="rounded-full px-2.5 py-0.5">
              {label}
            </Tag>
          </Tooltip>
        )
      },
    },
    {
      title: 'Ngày đăng ký',
      dataIndex: 'submitted_at',
      render: (v) => {
        const d = toDate(v)
        return d ? dayjs(d).format('DD/MM/YYYY') : '—'
      },
    },
    {
      title: 'Kết nối',
      key: 'presence',
      render: (_, record) => {
        const { status, text } = presenceInfo(record)
        const speed = speedText(record)
        return (
          <Space size={6}>
            <Badge status={status} text={text} />
            {speed && (
              <Tag bordered={false} color="blue" className="rounded-full px-2 py-0 text-[11px]">
                {speed}
              </Tag>
            )}
          </Space>
        )
      },
    },
    {
      title: 'Điểm vi phạm',
      key: 'points',
      width: 150,
      sorter: (a, b) => (driverPoints[a.id] || 0) - (driverPoints[b.id] || 0),
      render: (_, record) => {
        const p = driverPoints[record.id] || 0
        const level = levelOf(p, thresholds)
        return (
          <span className="flex items-center gap-2">
            <strong>{p}</strong>
            {level !== 'normal' && (
              <Tag color={LEVEL_META[level].color} bordered={false}>
                {LEVEL_META[level].label}
              </Tag>
            )}
          </span>
        )
      },
    },
    {
      title: 'Trạng thái',
      dataIndex: 'status',
      render: (value, record) => {
        const st = value ?? 'active'
        const meta = STATUS_META[st] ?? { label: st, color: 'default' }
        const tag = (
          <Tag color={meta.color} bordered={false} className="rounded-full px-2.5 py-0.5">
            {meta.label}
          </Tag>
        )
        return st === 'rejected' && record.reject_reason ? (
          <Tooltip title={`Lý do: ${record.reject_reason}`}>{tag}</Tooltip>
        ) : (
          tag
        )
      },
    },
    {
      title: '',
      key: 'actions',
      width: 180,
      align: 'right',
      render: (_, record) => {
        const st = record.status ?? 'active'
        if (st === 'pending') {
          const verified = !!record.email_verified
          return (
            <Space size={4}>
              <Popconfirm title="Duyệt tài khoản này?" okText="Duyệt" cancelText="Huỷ" onConfirm={() => handleApprove(record.id)}>
                <Tooltip title={!verified ? 'Email chưa xác thực — backend sẽ kiểm tra lại khi duyệt' : ''}>
                  <Button size="small" type="primary">Duyệt</Button>
                </Tooltip>
              </Popconfirm>
              <Button size="small" danger onClick={() => { setRejectTarget(record); setRejectReason('') }}>
                Từ chối
              </Button>
            </Space>
          )
        }
        if (st === 'active') {
          const moreItems = {
            items: [
              { key: 'reset', icon: <KeyOutlined />, label: 'Đặt lại mật khẩu', onClick: () => handleResetPassword(record) },
              { key: 'sound', icon: <SoundOutlined />, label: 'Phát loa cảnh báo', onClick: () => handleAlertSound(record) },
            ],
          }
          return (
            <Space size={4}>
              <Button size="small" onClick={() => openEdit(record)}>Sửa</Button>
              <Popconfirm title="Khoá tài khoản này?" okText="Khoá" cancelText="Huỷ" onConfirm={() => handleLock(record.id)}>
                <Button size="small" danger>Khoá</Button>
              </Popconfirm>
              <Dropdown menu={moreItems} trigger={['click']}>
                <Button size="small" icon={<DownOutlined />} />
              </Dropdown>
            </Space>
          )
        }
        if (st === 'inactive') {
          const moreItems = {
            items: [
              { key: 'reset', icon: <KeyOutlined />, label: 'Đặt lại mật khẩu', onClick: () => handleResetPassword(record) },
              {
                key: 'del', label: 'Xoá tài xế', danger: true,
                onClick: () => handleDelete(record.id),
              },
            ],
          }
          return (
            <Space size={4}>
              <Button size="small" type="primary" onClick={() => handleUnlock(record.id)}>Mở khoá</Button>
              <Dropdown menu={moreItems} trigger={['click']}>
                <Button size="small" icon={<DownOutlined />} />
              </Dropdown>
            </Space>
          )
        }
        return (
          <Popconfirm title="Xoá hồ sơ này?" okText="Xoá" cancelText="Huỷ" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger>Xoá</Button>
          </Popconfirm>
        )
      },
    },
  ]

  const segmentedOptions = [
    { value: 'all', label: `Tất cả (${counts.all})` },
    { value: 'pending', label: `Chờ duyệt (${counts.pending})` },
    { value: 'active', label: `Hoạt động (${counts.active})` },
    { value: 'inactive', label: `Đã khoá (${counts.inactive})` },
    { value: 'rejected', label: `Từ chối (${counts.rejected})` },
  ]

  return (
    <div>
      <PageHeader
        title="Quản lý tài khoản tài xế"
        subtitle="Duyệt hồ sơ đăng ký, khoá/mở khoá và theo dõi kết nối của tài xế"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            Thêm tài xế
          </Button>
        }
      />

      {error ? (
        <Alert
          className="mb-4"
          type="warning"
          showIcon
          message="Realtime chưa hoạt động"
          description="Không nghe được Firestore từ trình duyệt. Trang đang hiển thị dữ liệu tải một lần, sẽ không tự cập nhật."
        />
      ) : (
        <div className="mb-3 flex items-center gap-1.5 text-xs text-slate-400">
          <SyncOutlined spin />
          Đang đồng bộ realtime từ Firestore
        </div>
      )}

      {counts.pending > 0 && (
        <Alert
          className="mb-4"
          type="info"
          showIcon
          message={`Có ${counts.pending} hồ sơ đang chờ bạn duyệt.`}
          action={
            statusFilter !== 'pending' && (
              <Button size="small" type="link" onClick={() => setStatusFilter('pending')}>
                Xem ngay
              </Button>
            )
          }
        />
      )}

      {levelFilter && LEVEL_META[levelFilter] && (
        <Alert
          className="mb-4"
          type="info"
          showIcon
          closable
          onClose={() => setSearchParams({})}
          message={
            <>
              Đang xem tài xế mức <strong>{LEVEL_META[levelFilter].label}</strong> (
              {levelRange(levelFilter, thresholds)} tích luỹ): {filtered.length} người.{' '}
              <a onClick={() => setSearchParams({})}>Xem tất cả tài xế</a>
            </>
          }
        />
      )}

      <Card
        styles={{ body: { padding: 16 } }}
        className="mb-4"
      >
        <div className="flex flex-wrap items-center gap-3">
          <Input.Search
            allowClear
            placeholder="Tìm theo tên, SĐT, số bằng lái, email"
            defaultValue={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: 320 }}
          />
          <Segmented
            options={segmentedOptions}
            value={statusFilter}
            onChange={setStatusFilter}
          />
        </div>
      </Card>

      <Card styles={{ body: { padding: 0 } }}>
        <Table
          rowKey="id"
          loading={loading && !error}
          columns={columns}
          dataSource={filtered}
          pagination={{ pageSize: 10, showSizeChanger: false, hideOnSinglePage: true }}
        />
      </Card>

      {/* Modal thêm / sửa tài xế (admin tạo tay) */}
      <Modal
        open={modalOpen}
        title={editing ? 'Sửa tài xế' : 'Thêm tài xế'}
        onOk={handleSubmit}
        confirmLoading={saving}
        onCancel={() => setModalOpen(false)}
        okText="Lưu"
        cancelText="Huỷ"
        destroyOnHidden
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="Họ tên"
            rules={[{ required: true, message: 'Nhập họ tên' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="phone"
            label="Số điện thoại"
            rules={[{ required: true, message: 'Nhập số điện thoại' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="license_number"
            label="Số bằng lái"
            rules={[{ required: true, message: 'Nhập số bằng lái' }]}
          >
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      {/* Modal từ chối */}
      <Modal
        open={!!rejectTarget}
        title={`Từ chối tài khoản: ${rejectTarget?.name ?? ''}`}
        onOk={handleReject}
        onCancel={() => setRejectTarget(null)}
        okText="Từ chối"
        okButtonProps={{ danger: true }}
        cancelText="Huỷ"
        destroyOnHidden
      >
        <p className="mb-2 text-sm text-gray-500">
          Lý do sẽ hiển thị cho tài xế trên app.
        </p>
        <Input.TextArea
          rows={3}
          value={rejectReason}
          onChange={(e) => setRejectReason(e.target.value)}
          placeholder="Ví dụ: Số bằng lái không hợp lệ"
        />
      </Modal>
    </div>
  )
}

export default Drivers
