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
} from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import {
  createDriver,
  deleteDriver,
  listDrivers,
  updateDriver,
} from '../services/drivers'
import { toDate, useDriversRealtime } from '../hooks/useDriversRealtime'

const STATUS_OPTIONS = [
  { value: 'active', label: 'Đang hoạt động' },
  { value: 'inactive', label: 'Ngừng hoạt động' },
]

const statusLabel = (value) =>
  STATUS_OPTIONS.find((o) => o.value === value)?.label ?? value

// Coi là mất kết nối nếu app tài xế không báo tín hiệu trong ngần này (app
// crash không kịp gửi "offline").
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
  const [form] = Form.useForm()

  // Realtime hỏng (thường do Firestore rules chưa mở cho client) -> tải 1 lần
  // qua backend để trang vẫn dùng được.
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
    return rows.filter((d) => {
      const status = d.status ?? 'active'
      if (statusFilter !== 'all' && status !== statusFilter) return false
      if (!q) return true
      return [d.name, d.phone, d.license_number]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(q))
    })
  }, [rows, search, statusFilter])

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({ status: 'active' })
    setModalOpen(true)
  }

  const openEdit = (record) => {
    setEditing(record)
    form.setFieldsValue({
      name: record.name,
      phone: record.phone,
      license_number: record.license_number,
      status: record.status ?? 'active',
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
        await createDriver(values)
        message.success('Đã thêm tài xế')
      }
      setModalOpen(false)
      // Không cần reload: onSnapshot tự đẩy bản ghi mới về.
    } catch (e) {
      message.error(e.message)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id) => {
    try {
      await deleteDriver(id)
      message.success('Đã xoá tài xế')
    } catch (e) {
      message.error(e.message)
    }
  }

  const columns = [
    { title: 'Họ tên', dataIndex: 'name' },
    { title: 'Số điện thoại', dataIndex: 'phone' },
    { title: 'Số bằng lái', dataIndex: 'license_number' },
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
      render: (value) => {
        const status = value ?? 'active'
        return (
          <Tag color={status === 'active' ? 'green' : 'default'}>
            {statusLabel(status)}
          </Tag>
        )
      },
    },
    {
      title: '',
      key: 'actions',
      width: 150,
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => openEdit(record)}>
            Sửa
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
      ),
    },
  ]

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <h1 className="text-xl font-semibold text-gray-800">Quản lý tài xế</h1>
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
          description="Không nghe được Firestore từ trình duyệt (thường do chưa deploy firestore.rules). Trang đang hiển thị dữ liệu tải một lần, sẽ không tự cập nhật."
        />
      ) : (
        <div className="mb-3 text-xs text-gray-500">
          <Badge status="processing" text="Đang cập nhật realtime từ Firestore" />
        </div>
      )}

      <Space className="mb-4" wrap>
        <Input.Search
          allowClear
          placeholder="Tìm theo tên, SĐT, số bằng lái"
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: 280 }}
        />
        <Select
          value={statusFilter}
          onChange={setStatusFilter}
          style={{ width: 190 }}
          options={[
            { value: 'all', label: 'Tất cả trạng thái' },
            ...STATUS_OPTIONS,
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
          <Form.Item name="status" label="Trạng thái">
            <Select options={STATUS_OPTIONS} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Drivers
