import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  App,
  Button,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
} from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { listDrivers } from '../services/drivers'
import {
  createVehicle,
  deleteVehicle,
  listVehicles,
  updateVehicle,
} from '../services/vehicles'
import PageHeader from '../components/PageHeader'

const STATUS_OPTIONS = [
  { value: 'active', label: 'Đang chạy' },
  { value: 'maintenance', label: 'Đang bảo trì' },
  { value: 'inactive', label: 'Ngừng sử dụng' },
]

const STATUS_COLOR = { active: 'green', maintenance: 'orange', inactive: 'default' }

const statusLabel = (value) =>
  STATUS_OPTIONS.find((o) => o.value === value)?.label ?? value

function Vehicles() {
  const { message } = App.useApp()
  const [rows, setRows] = useState([])
  const [drivers, setDrivers] = useState([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm()

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [vehicleList, driverList] = await Promise.all([
        listVehicles(),
        listDrivers(),
      ])
      setRows(vehicleList)
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

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return rows.filter((v) => {
      const status = v.status ?? 'active'
      if (statusFilter !== 'all' && status !== statusFilter) return false
      if (!q) return true
      return [v.plate_number, v.brand, v.model]
        .filter(Boolean)
        .some((x) => String(x).toLowerCase().includes(q))
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
      plate_number: record.plate_number,
      brand: record.brand,
      model: record.model,
      year: record.year ?? null,
      status: record.status ?? 'active',
      driver_id: record.driver_id ?? null,
      current_odometer_km: record.current_odometer_km ?? null,
      note: record.note ?? '',
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
        await updateVehicle(editing.id, values)
        message.success('Đã cập nhật xe')
      } else {
        await createVehicle(values)
        message.success('Đã thêm xe')
      }
      setModalOpen(false)
      load()
    } catch (e) {
      message.error(e.message)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id) => {
    try {
      await deleteVehicle(id)
      message.success('Đã xoá xe')
      load()
    } catch (e) {
      message.error(e.message)
    }
  }

  const columns = [
    { title: 'Biển số', dataIndex: 'plate_number' },
    { title: 'Hãng', dataIndex: 'brand' },
    { title: 'Dòng xe', dataIndex: 'model' },
    { title: 'Năm SX', dataIndex: 'year', render: (y) => y || '—' },
    {
      title: 'Số km hiện tại',
      dataIndex: 'current_odometer_km',
      render: (v) => (v == null ? '—' : `${v.toLocaleString('vi-VN')} km`),
    },
    {
      title: 'Tài xế phụ trách',
      dataIndex: 'driver_id',
      render: (id) => driverName[id] || '—',
    },
    {
      title: 'Trạng thái',
      dataIndex: 'status',
      render: (value) => {
        const status = value ?? 'active'
        return <Tag color={STATUS_COLOR[status]}>{statusLabel(status)}</Tag>
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
            title="Xoá xe này?"
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
      <PageHeader
        title="Danh mục xe"
        subtitle="Quản lý đội xe và phân công tài xế"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            Thêm xe
          </Button>
        }
      />

      <Space className="mb-4" wrap>
        <Input.Search
          allowClear
          placeholder="Tìm theo biển số, hãng, dòng xe"
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
        loading={loading}
        columns={columns}
        dataSource={filtered}
        pagination={{ pageSize: 10, showSizeChanger: false }}
      />

      <Modal
        open={modalOpen}
        title={editing ? 'Sửa xe' : 'Thêm xe'}
        onOk={handleSubmit}
        confirmLoading={saving}
        onCancel={() => setModalOpen(false)}
        okText="Lưu"
        cancelText="Huỷ"
        destroyOnHidden
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="plate_number"
            label="Biển số"
            rules={[{ required: true, message: 'Nhập biển số' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="brand"
            label="Hãng"
            rules={[{ required: true, message: 'Nhập hãng xe' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="model"
            label="Dòng xe"
            rules={[{ required: true, message: 'Nhập dòng xe' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item name="year" label="Năm sản xuất">
            <InputNumber min={1980} max={2100} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="current_odometer_km"
            label="Số km hiện tại (đồng hồ công-tơ-mét)"
            tooltip="Dùng để hệ thống tự nhắc bảo trì/đăng kiểm khi xe gần tới hạn theo km"
          >
            <InputNumber min={0} style={{ width: '100%' }} addonAfter="km" />
          </Form.Item>
          <Form.Item name="driver_id" label="Tài xế phụ trách">
            <Select
              allowClear
              placeholder="Chưa gán"
              options={drivers.map((d) => ({ value: d.id, label: d.name }))}
            />
          </Form.Item>
          <Form.Item name="status" label="Trạng thái">
            <Select options={STATUS_OPTIONS} />
          </Form.Item>
          <Form.Item name="note" label="Ghi chú">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Vehicles
