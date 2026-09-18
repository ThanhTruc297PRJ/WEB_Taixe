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
  Radio,
  Select,
  Space,
  Table,
  Tag,
} from 'antd'
import { BellOutlined, CheckCircleOutlined, PlusOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { listVehicles } from '../services/vehicles'
import { listDrivers } from '../services/drivers'
import {
  completeInspection,
  createInspection,
  deleteInspection,
  listInspections,
  notifyInspection,
  updateInspection,
} from '../services/inspections'
import PageHeader from '../components/PageHeader'

const NOTIFY_REASON = {
  driver_has_no_fcm_token: 'Chưa gán người phụ trách hoặc chưa có thiết bị nhận thông báo',
  vehicle_not_found: 'Không tìm thấy xe',
  inspection_not_found: 'Không tìm thấy hồ sơ đăng kiểm',
}

const RESULT_META = {
  passed: { label: 'Đạt', color: 'green' },
  failed: { label: 'Không đạt', color: 'red' },
}

// Quá hạn khi tem cũ đã hết hạn mà vẫn chưa đăng kiểm xong.
const isOverdue = (record) =>
  record.status === 'pending' &&
  dayjs(record.old_sticker_expiry).isBefore(dayjs(), 'day')

function Inspections() {
  const { message } = App.useApp()
  const [rows, setRows] = useState([])
  const [vehicles, setVehicles] = useState([])
  const [drivers, setDrivers] = useState([])
  const [loading, setLoading] = useState(false)
  const [statusFilter, setStatusFilter] = useState('all')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [saving, setSaving] = useState(false)
  const [notifyingId, setNotifyingId] = useState(null)
  const [completeTarget, setCompleteTarget] = useState(null)
  const [completing, setCompleting] = useState(false)
  const [form] = Form.useForm()
  const [completeForm] = Form.useForm()

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [inspectionList, vehicleList, driverList] = await Promise.all([
        listInspections(),
        listVehicles(),
        listDrivers(),
      ])
      setRows(inspectionList)
      setVehicles(vehicleList)
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

  const vehiclePlate = useMemo(() => {
    const map = {}
    for (const v of vehicles) map[v.id] = v.plate_number
    return map
  }, [vehicles])

  const driverName = useMemo(() => {
    const map = {}
    for (const d of drivers) map[d.id] = d.name
    return map
  }, [drivers])

  const filtered = useMemo(() => {
    const sorted = [...rows].sort(
      (a, b) => dayjs(a.old_sticker_expiry).valueOf() - dayjs(b.old_sticker_expiry).valueOf(),
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
    form.setFieldsValue({ remind_days_before: 15 })
    setModalOpen(true)
  }

  const openEdit = (record) => {
    setEditing(record)
    form.setFieldsValue({
      vehicle_id: record.vehicle_id,
      driver_id: record.driver_id ?? null,
      station: record.station,
      appointment_at: record.appointment_at ? dayjs(record.appointment_at) : null,
      old_sticker_expiry: record.old_sticker_expiry ? dayjs(record.old_sticker_expiry) : null,
      remind_days_before: record.remind_days_before ?? 15,
      inspection_fee: record.inspection_fee ?? null,
      road_fee: record.road_fee ?? null,
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
      appointment_at: values.appointment_at ? values.appointment_at.toISOString() : null,
      old_sticker_expiry: values.old_sticker_expiry.toISOString(),
    }
    setSaving(true)
    try {
      if (editing) {
        await updateInspection(editing.id, payload)
        message.success('Đã cập nhật hồ sơ đăng kiểm')
      } else {
        await createInspection(payload)
        message.success('Đã thêm hồ sơ đăng kiểm')
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
      await deleteInspection(id)
      message.success('Đã xoá hồ sơ đăng kiểm')
      load()
    } catch (e) {
      message.error(e.message)
    }
  }

  const handleNotify = async (id) => {
    setNotifyingId(id)
    try {
      const result = await notifyInspection(id)
      if (result.sent) {
        message.success('Đã gửi nhắc đăng kiểm')
      } else {
        message.warning(NOTIFY_REASON[result.reason] || `Không gửi được: ${result.reason}`)
      }
    } catch (e) {
      message.error(e.message)
    } finally {
      setNotifyingId(null)
    }
  }

  const openComplete = (record) => {
    setCompleteTarget(record)
    completeForm.resetFields()
    completeForm.setFieldsValue({ result: 'passed' })
  }

  const handleComplete = async () => {
    let values
    try {
      values = await completeForm.validateFields()
    } catch {
      return
    }
    setCompleting(true)
    try {
      const payload = {
        result: values.result,
        new_sticker_expiry:
          values.result === 'passed' && values.new_sticker_expiry
            ? values.new_sticker_expiry.toISOString()
            : null,
      }
      const outcome = await completeInspection(completeTarget.id, payload)
      message.success(
        outcome.next
          ? 'Đã đóng hồ sơ — tự tạo hồ sơ đăng kiểm kỳ tiếp theo'
          : 'Đã đóng hồ sơ',
      )
      setCompleteTarget(null)
      load()
    } catch (e) {
      message.error(e.message)
    } finally {
      setCompleting(false)
    }
  }

  const columns = [
    { title: 'Xe', dataIndex: 'vehicle_id', render: (id) => vehiclePlate[id] || id },
    {
      title: 'Người phụ trách',
      dataIndex: 'driver_id',
      render: (id) => driverName[id] || '—',
    },
    { title: 'Trạm đăng kiểm', dataIndex: 'station' },
    {
      title: 'Khung giờ hẹn',
      dataIndex: 'appointment_at',
      render: (d) => (d ? dayjs(d).format('DD/MM/YYYY HH:mm') : 'Chưa đặt lịch'),
    },
    {
      title: 'Tem cũ hết hạn',
      dataIndex: 'old_sticker_expiry',
      render: (d) => dayjs(d).format('DD/MM/YYYY'),
    },
    {
      title: 'Chi phí',
      key: 'cost',
      render: (_, r) => {
        const total = (r.inspection_fee || 0) + (r.road_fee || 0)
        return total ? `${total.toLocaleString('vi-VN')}đ` : '—'
      },
    },
    {
      title: 'Kết quả',
      dataIndex: 'result',
      render: (v) =>
        v ? <Tag color={RESULT_META[v]?.color}>{RESULT_META[v]?.label}</Tag> : '—',
    },
    {
      title: 'Trạng thái',
      key: 'status',
      render: (_, record) => {
        if (record.status === 'done') return <Tag color="green">Đã xong</Tag>
        if (isOverdue(record)) return <Tag color="red">Quá hạn tem</Tag>
        return <Tag color="blue">Chờ tới hạn</Tag>
      },
    },
    {
      title: '',
      key: 'actions',
      width: 320,
      render: (_, record) => (
        <Space wrap>
          <Button
            size="small"
            icon={<BellOutlined />}
            loading={notifyingId === record.id}
            disabled={record.status === 'done'}
            onClick={() => handleNotify(record.id)}
          >
            Gửi nhắc
          </Button>
          {record.status === 'pending' && (
            <Button
              size="small"
              type="primary"
              icon={<CheckCircleOutlined />}
              onClick={() => openComplete(record)}
            >
              Đóng hồ sơ
            </Button>
          )}
          <Button size="small" onClick={() => openEdit(record)}>
            Sửa
          </Button>
          <Popconfirm
            title="Xoá hồ sơ đăng kiểm này?"
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
        title="Đăng kiểm xe"
        subtitle="Trạm hẹn, hạn tem và chi phí đăng kiểm — tách riêng khỏi lịch bảo trì"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            Thêm hồ sơ đăng kiểm
          </Button>
        }
      />

      <Space className="mb-4" wrap>
        <Select
          value={statusFilter}
          onChange={setStatusFilter}
          style={{ width: 200 }}
          options={[
            { value: 'all', label: 'Tất cả' },
            { value: 'overdue', label: 'Quá hạn tem' },
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
        scroll={{ x: 1100 }}
      />

      <Modal
        open={modalOpen}
        title={editing ? 'Sửa hồ sơ đăng kiểm' : 'Thêm hồ sơ đăng kiểm'}
        onOk={handleSubmit}
        confirmLoading={saving}
        onCancel={() => setModalOpen(false)}
        okText="Lưu"
        cancelText="Huỷ"
        width={600}
        styles={{ body: { maxHeight: '70vh', overflowY: 'auto', paddingRight: 4 } }}
        destroyOnHidden
      >
        <Form form={form} layout="vertical">
          <div className="grid grid-cols-2 gap-x-3">
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
              name="driver_id"
              label="Người phụ trách mang xe đi"
              tooltip="Có thể khác tài xế thường lái xe này"
            >
              <Select
                allowClear
                placeholder="Chưa gán"
                options={drivers.map((d) => ({ value: d.id, label: d.name }))}
              />
            </Form.Item>
          </div>

          <Form.Item
            name="station"
            label="Trạm đăng kiểm"
            rules={[{ required: true, message: 'Nhập trạm đăng kiểm' }]}
          >
            <Input placeholder="vd: Trạm đăng kiểm 50-03V" />
          </Form.Item>

          <div className="grid grid-cols-2 gap-x-3">
            <Form.Item
              name="appointment_at"
              label="Khung giờ hẹn"
              tooltip="Có thể để trống nếu chưa liên hệ trạm đặt lịch — điền sau"
            >
              <DatePicker
                showTime
                format="DD/MM/YYYY HH:mm"
                style={{ width: '100%' }}
                placeholder="Chưa đặt lịch"
              />
            </Form.Item>
            <Form.Item
              name="old_sticker_expiry"
              label="Tem cũ hết hạn"
              rules={[{ required: true, message: 'Chọn ngày hết hạn tem cũ' }]}
              tooltip="Hệ thống tự nhắc trước theo ngày này — không cần tự nhớ đặt lịch sớm"
            >
              <DatePicker format="DD/MM/YYYY" style={{ width: '100%' }} />
            </Form.Item>
          </div>

          <Form.Item
            name="remind_days_before"
            label="Báo trước mấy ngày (tính từ hạn tem)"
            rules={[{ required: true }]}
          >
            <InputNumber min={0} style={{ width: '100%' }} addonAfter="ngày" />
          </Form.Item>

          <div className="grid grid-cols-2 gap-x-3">
            <Form.Item name="inspection_fee" label="Phí kiểm định">
              <InputNumber min={0} style={{ width: '100%' }} addonAfter="đ" />
            </Form.Item>
            <Form.Item name="road_fee" label="Phí bảo trì đường bộ">
              <InputNumber min={0} style={{ width: '100%' }} addonAfter="đ" />
            </Form.Item>
          </div>

          <Form.Item name="note" label="Ghi chú">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        open={!!completeTarget}
        title={`Đóng hồ sơ đăng kiểm: ${completeTarget ? vehiclePlate[completeTarget.vehicle_id] : ''}`}
        onOk={handleComplete}
        confirmLoading={completing}
        onCancel={() => setCompleteTarget(null)}
        okText="Đóng hồ sơ"
        cancelText="Huỷ"
        destroyOnHidden
      >
        <Form form={completeForm} layout="vertical">
          <Form.Item name="result" label="Kết quả đăng kiểm" rules={[{ required: true }]}>
            <Radio.Group
              options={[
                { value: 'passed', label: 'Đạt' },
                { value: 'failed', label: 'Không đạt' },
              ]}
              optionType="button"
            />
          </Form.Item>
          <Form.Item
            noStyle
            shouldUpdate={(prev, cur) => prev.result !== cur.result}
          >
            {({ getFieldValue }) =>
              getFieldValue('result') === 'passed' ? (
                <Form.Item
                  name="new_sticker_expiry"
                  label="Hạn tem mới (nếu có)"
                  tooltip="Điền để hệ thống tự tạo hồ sơ đăng kiểm cho kỳ tiếp theo"
                >
                  <DatePicker format="DD/MM/YYYY" style={{ width: '100%' }} />
                </Form.Item>
              ) : (
                <p className="text-sm text-slate-500 mb-0">
                  Xe cần sửa chữa rồi đặt lịch đăng kiểm lại — tạo hồ sơ mới sau khi có lịch hẹn.
                </p>
              )
            }
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Inspections
