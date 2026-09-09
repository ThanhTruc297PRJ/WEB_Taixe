import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  App,
  Badge,
  Button,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  Tooltip,
} from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import {
  approveDriver,
  createDriver,
  deleteDriver,
  listDrivers,
  lockDriver,
  rejectDriver,
  unlockDriver,
  updateDriver,
} from '../services/drivers'
import { toDate, useDriversRealtime } from '../hooks/useDriversRealtime'

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

function Drivers() {
  const { message } = App.useApp()
  const { drivers: liveDrivers, loading, error } = useDriversRealtime()
  const [fallback, setFallback] = useState(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [saving, setSaving] = useState(false)
  const [rejectTarget, setRejectTarget] = useState(null)
  const [rejectReason, setRejectReason] = useState('')
  const [form] = Form.useForm()

  useEffect(() => {
    if (!error) return
    message.warning('Không nghe được realtime từ Firestore — dùng dữ liệu tải một lần.')
    listDrivers()
      .then(setFallback)
      .catch((e) => message.error(e.message))
  }, [error, message])

  const rows = useMemo(
    () => (error ? (fallback ?? []) : liveDrivers),
    [error, fallback, liveDrivers],
  )

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    const result = rows.filter((d) => {
      const status = d.status ?? 'active'
      if (statusFilter !== 'all' && status !== statusFilter) return false
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
  }, [rows, search, statusFilter])

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
    { title: 'Họ tên', dataIndex: 'name' },
    { title: 'Số điện thoại', dataIndex: 'phone' },
    { title: 'Số bằng lái', dataIndex: 'license_number' },
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
        return <Badge status={status} text={text} />
      },
    },
    {
      title: 'Trạng thái',
      dataIndex: 'status',
      render: (value, record) => {
        const st = value ?? 'active'
        const meta = STATUS_META[st] ?? { label: st, color: 'default' }
        const tag = <Tag color={meta.color}>{meta.label}</Tag>
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
      width: 190,
      render: (_, record) => {
        const st = record.status ?? 'active'
        if (st === 'pending') {
          return (
            <Space>
              <Popconfirm
                title="Duyệt tài khoản này?"
                okText="Duyệt"
                cancelText="Huỷ"
                onConfirm={() => handleApprove(record.id)}
              >
                <Button size="small" type="primary">
                  Duyệt
                </Button>
              </Popconfirm>
              <Button
                size="small"
                danger
                onClick={() => {
                  setRejectTarget(record)
                  setRejectReason('')
                }}
              >
                Từ chối
              </Button>
            </Space>
          )
        }
        if (st === 'active') {
          return (
            <Space>
              <Button size="small" onClick={() => openEdit(record)}>
                Sửa
              </Button>
              <Popconfirm
                title="Khoá tài khoản này?"
                okText="Khoá"
                cancelText="Huỷ"
                onConfirm={() => handleLock(record.id)}
              >
                <Button size="small" danger>
                  Khoá
                </Button>
              </Popconfirm>
            </Space>
          )
        }
        if (st === 'inactive') {
          return (
            <Space>
              <Button size="small" type="primary" onClick={() => handleUnlock(record.id)}>
                Mở khoá
              </Button>
              <Popconfirm
                title="Xoá tài xế này?"
                okText="Xoá"
                cancelText="Huỷ"
                onConfirm={() => handleDelete(record.id)}
              >
                <Button size="small" danger>
                  Xoá
                </Button>
              </Popconfirm>
            </Space>
          )
        }
        return (
          <Popconfirm
            title="Xoá hồ sơ này?"
            okText="Xoá"
            cancelText="Huỷ"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button size="small" danger>
              Xoá
            </Button>
          </Popconfirm>
        )
      },
    },
  ]

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <h1 className="text-xl font-semibold text-gray-800">Quản lý tài khoản tài xế</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          Thêm tài xế
        </Button>
      </div>

      {error ? (
        <Alert
          className="mb-4"
          type="warning"
          showIcon
          message="Realtime chưa hoạt động"
          description="Không nghe được Firestore từ trình duyệt. Trang đang hiển thị dữ liệu tải một lần, sẽ không tự cập nhật."
        />
      ) : (
        <div className="mb-3 text-xs text-gray-500">
          <Badge status="processing" text="Đang cập nhật realtime từ Firestore" />
        </div>
      )}

      <Space className="mb-4" wrap>
        <Input.Search
          allowClear
          placeholder="Tìm theo tên, SĐT, số bằng lái, email"
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: 300 }}
        />
        <Select
          value={statusFilter}
          onChange={setStatusFilter}
          style={{ width: 190 }}
          options={[
            { value: 'all', label: 'Tất cả' },
            { value: 'pending', label: 'Chờ duyệt' },
            { value: 'active', label: 'Đang hoạt động' },
            { value: 'inactive', label: 'Đã khoá' },
            { value: 'rejected', label: 'Đã từ chối' },
          ]}
        />
      </Space>

      <Table
        rowKey="id"
        loading={loading && !error}
        columns={columns}
        dataSource={filtered}
        pagination={{ pageSize: 10, showSizeChanger: false }}
      />

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
