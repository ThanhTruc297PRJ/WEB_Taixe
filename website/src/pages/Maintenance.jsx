import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  App,
  Button,
  DatePicker,
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
import { BellOutlined, PlusOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { listVehicles } from '../services/vehicles'
import {
  createMaintenance,
  deleteMaintenance,
  listMaintenance,
  notifyMaintenance,
  updateMaintenance,
} from '../services/maintenance'

const TYPE_OPTIONS = [
  { value: 'oil_change', label: 'Thay dầu' },
  { value: 'tire', label: 'Kiểm tra/thay lốp' },
  { value: 'inspection', label: 'Đăng kiểm' },
  { value: 'other', label: 'Bảo trì khác' },
]

const typeLabel = (value) =>
  TYPE_OPTIONS.find((o) => o.value === value)?.label ?? value

const NOTIFY_REASON = {
  driver_has_no_fcm_token: 'Xe chưa gán tài xế hoặc tài xế chưa có thiết bị nhận thông báo',
  vehicle_not_found: 'Không tìm thấy xe',
  maintenance_not_found: 'Không tìm thấy lịch bảo trì',
}

const isOverdue = (record) =>
  record.status === 'pending' &&
  dayjs(record.scheduled_date).isBefore(dayjs(), 'day')

function Maintenance() {
  const { message } = App.useApp()
  const [rows, setRows] = useState([])
  const [vehicles, setVehicles] = useState([])
  const [loading, setLoading] = useState(false)
  const [statusFilter, setStatusFilter] = useState('all')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [saving, setSaving] = useState(false)
  const [notifyingId, setNotifyingId] = useState(null)
  const [form] = Form.useForm()

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [maintenanceList, vehicleList] = await Promise.all([
        listMaintenance(),
        listVehicles(),
      ])
      setRows(maintenanceList)
      setVehicles(vehicleList)
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

  const vehiclePlate = useMemo(() => {
    const map = {}
    for (const v of vehicles) map[v.id] = v.plate_number
    return map
  }, [vehicles])

  const filtered = useMemo(() => {
    const sorted = [...rows].sort((a, b) =>
      dayjs(a.scheduled_date).valueOf() - dayjs(b.scheduled_date).valueOf(),
    )
    if (statusFilter === 'all') return sorted
    if (statusFilter === 'overdue') return sorted.filter(isOverdue)
    if (statusFilter === 'pending')
      return sorted.filter((r) => r.status === 'pending' && !isOverdue(r))
    return sorted.filter((r) => r.status === statusFilter)
  }, [rows, statusFilter])

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({ type: 'oil_change', status: 'pending' })
    setModalOpen(true)
  }

  const openEdit = (record) => {
    setEditing(record)
    form.setFieldsValue({
      vehicle_id: record.vehicle_id,
      type: record.type,
      scheduled_date: record.scheduled_date ? dayjs(record.scheduled_date) : null,
      status: record.status ?? 'pending',
      odometer: record.odometer ?? null,
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
    const payload = {
      ...values,
      scheduled_date: values.scheduled_date.toISOString(),
    }
    setSaving(true)
    try {
      if (editing) {
        await updateMaintenance(editing.id, payload)
        message.success('Đã cập nhật lịch bảo trì')
      } else {
        await createMaintenance(payload)
        message.success('Đã thêm lịch bảo trì')
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
      await deleteMaintenance(id)
      message.success('Đã xoá lịch bảo trì')
      load()
    } catch (e) {
      message.error(e.message)
    }
  }

  const handleNotify = async (id) => {
    setNotifyingId(id)
    try {
      const result = await notifyMaintenance(id)
      if (result.sent) {
        message.success('Đã gửi nhắc bảo trì tới tài xế')
      } else {
        message.warning(NOTIFY_REASON[result.reason] || `Không gửi được: ${result.reason}`)
      }
    } catch (e) {
      message.error(e.message)
    } finally {
      setNotifyingId(null)
    }
  }

  const columns = [
    {
      title: 'Xe',
      dataIndex: 'vehicle_id',
      render: (id) => vehiclePlate[id] || id,
    },
    { title: 'Hạng mục', dataIndex: 'type', render: typeLabel },
    {
      title: 'Ngày hẹn',
      dataIndex: 'scheduled_date',
      render: (d) => dayjs(d).format('DD/MM/YYYY'),
    },
    { title: 'Số km', dataIndex: 'odometer', render: (v) => v ?? '—' },
    {
      title: 'Trạng thái',
      key: 'status',
      render: (_, record) => {
        if (record.status === 'done') return <Tag color="green">Đã xong</Tag>
        if (isOverdue(record)) return <Tag color="red">Quá hạn</Tag>
        return <Tag color="blue">Chờ tới hạn</Tag>
      },
    },
    {
      title: '',
      key: 'actions',
      width: 240,
      render: (_, record) => (
        <Space>
          <Button
            size="small"
            icon={<BellOutlined />}
            loading={notifyingId === record.id}
            disabled={record.status === 'done'}
            onClick={() => handleNotify(record.id)}
          >
            Gửi nhắc
          </Button>
          <Button size="small" onClick={() => openEdit(record)}>
            Sửa
          </Button>
          <Popconfirm
            title="Xoá lịch bảo trì này?"
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
        <h1 className="text-xl font-semibold text-gray-800">
          Lịch bảo trì xe
        </h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          Thêm lịch bảo trì
        </Button>
      </div>

      <Space className="mb-4" wrap>
        <Select
          value={statusFilter}
          onChange={setStatusFilter}
          style={{ width: 200 }}
          options={[
            { value: 'all', label: 'Tất cả' },
            { value: 'overdue', label: 'Quá hạn' },
            { value: 'pending', label: 'Chờ tới hạn' },
            { value: 'done', label: 'Đã xong' },
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
        title={editing ? 'Sửa lịch bảo trì' : 'Thêm lịch bảo trì'}
        onOk={handleSubmit}
        confirmLoading={saving}
        onCancel={() => setModalOpen(false)}
        okText="Lưu"
        cancelText="Huỷ"
        destroyOnHidden
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="vehicle_id"
            label="Xe"
            rules={[{ required: true, message: 'Chọn xe' }]}
          >
            <Select
              placeholder="Chọn xe"
              options={vehicles.map((v) => ({
                value: v.id,
                label: `${v.plate_number} — ${v.brand} ${v.model}`,
              }))}
            />
          </Form.Item>
          <Form.Item
            name="type"
            label="Hạng mục"
            rules={[{ required: true, message: 'Chọn hạng mục' }]}
          >
            <Select options={TYPE_OPTIONS} />
          </Form.Item>
          <Form.Item
            name="scheduled_date"
            label="Ngày hẹn"
            rules={[{ required: true, message: 'Chọn ngày hẹn' }]}
          >
            <DatePicker format="DD/MM/YYYY" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="odometer" label="Số km (odometer)">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="status" label="Trạng thái">
            <Select
              options={[
                { value: 'pending', label: 'Chờ tới hạn' },
                { value: 'done', label: 'Đã xong' },
              ]}
            />
          </Form.Item>
          <Form.Item name="note" label="Ghi chú">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Maintenance
