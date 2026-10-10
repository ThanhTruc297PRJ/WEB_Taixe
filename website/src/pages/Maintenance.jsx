import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  App,
  Alert,
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
} from 'antd'
import { AuditOutlined, BellOutlined, PlusOutlined, SyncOutlined } from '@ant-design/icons'
import { useSearchParams } from 'react-router-dom'
import dayjs from 'dayjs'
import { listVehicles } from '../services/vehicles'
import { listDrivers } from '../services/drivers'
import { getSettings } from '../services/settings'
import {
  createMaintenance,
  deleteMaintenance,
  listMaintenance,
  notifyMaintenance,
  scanReminders,
  updateMaintenance,
} from '../services/maintenance'
import PageHeader from '../components/PageHeader'
import JobReviewModal, { JobStatusTag } from '../components/JobReviewModal'
import {
  FORM_GRID,
  FULLSCREEN_FORM_STYLE,
  FULLSCREEN_MODAL,
} from '../config/fullscreenModal'

// "Đăng kiểm" đã tách sang trang riêng (Đăng kiểm xe) — không còn chọn được
// khi tạo mới, chỉ giữ nhãn cho dữ liệu cũ (xem _TYPE_LABELS phía backend).
const TYPE_OPTIONS = [
  { value: 'oil_change', label: 'Thay dầu' },
  { value: 'tire', label: 'Kiểm tra/thay lốp' },
  { value: 'brake', label: 'Phanh/thắng' },
  { value: 'battery', label: 'Ắc quy' },
  { value: 'other', label: 'Bảo trì khác' },
]

const typeLabel = (value) =>
  TYPE_OPTIONS.find((o) => o.value === value)?.label ??
  (value === 'inspection' ? 'Đăng kiểm (dữ liệu cũ)' : value)

const NOTIFY_REASON = {
  driver_has_no_fcm_token:
    'Xe chưa gán tài xế hoặc tài xế chưa có thiết bị nhận thông báo',
  vehicle_not_found: 'Không tìm thấy xe',
  maintenance_not_found: 'Không tìm thấy lịch bảo trì',
}

const isOverdue = (record) =>
  record.status === 'pending' &&
  dayjs(record.scheduled_date).isBefore(dayjs(), 'day')

// "Sắp / đã tới hạn": còn chờ và đã vào khoảng báo trước theo NGÀY hoặc theo
// KM — cùng điều kiện với chuông thông báo và ô Bảo trì ở trang Tổng quan
// (backend maintenance_service.list_upcoming), nên số lượng luôn khớp.
const isDueSoon = (record, vehicleKm) => {
  if (record.status !== 'pending') return false
  if (record.scheduled_date) {
    const daysLeft = dayjs(record.scheduled_date).diff(dayjs(), 'hour') / 24
    if (daysLeft <= (record.remind_days_before ?? 7)) return true
  }
  if (record.due_odometer_km != null && vehicleKm != null) {
    if (record.due_odometer_km - vehicleKm <= (record.remind_km_before ?? 500))
      return true
  }
  return false
}

function Maintenance() {
  const { message } = App.useApp()
  const [searchParams, setSearchParams] = useSearchParams()
  const vehicleFilter = searchParams.get('vehicle_id')
  const [rows, setRows] = useState([])
  const [vehicles, setVehicles] = useState([])
  const [drivers, setDrivers] = useState([])
  const [loading, setLoading] = useState(false)
  const statusFilter = searchParams.get('status') || 'all'
  const setStatusFilter = (value) =>
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      if (value && value !== 'all') next.set('status', value)
      else next.delete('status')
      return next
    })
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [saving, setSaving] = useState(false)
  const [notifyingId, setNotifyingId] = useState(null)
  const [scanning, setScanning] = useState(false)
  const [reminderDefaults, setReminderDefaults] = useState({
    remind_days_before: 7,
    remind_km_before: 500,
  })
  const [form] = Form.useForm()

  useEffect(() => {
    getSettings()
      .then((s) => setReminderDefaults(s.maintenance_defaults))
      .catch(() => {
        /* giữ mặc định cứng nếu tải cấu hình lỗi */
      })
  }, [])

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [maintenanceList, vehicleList, driverList] = await Promise.all([
        listMaintenance(),
        listVehicles(),
        listDrivers(),
      ])
      setRows(maintenanceList)
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

  const vehicleKm = useMemo(() => {
    const map = {}
    for (const v of vehicles) map[v.id] = v.current_odometer_km
    return map
  }, [vehicles])

  const driverName = useMemo(() => {
    const map = {}
    for (const d of drivers) map[d.id] = d.name
    return map
  }, [drivers])

  // ?review=<id> mở thẳng màn xác nhận (link từ chuông thông báo).
  const reviewId = searchParams.get('review')
  const reviewTarget = reviewId ? rows.find((r) => r.id === reviewId) : null
  const setReviewId = (id) =>
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      if (id) next.set('review', id)
      else next.delete('review')
      return next
    })

  const filtered = useMemo(() => {
    let sorted = [...rows].sort(
      (a, b) =>
        dayjs(a.scheduled_date).valueOf() - dayjs(b.scheduled_date).valueOf(),
    )
    if (vehicleFilter)
      sorted = sorted.filter((r) => r.vehicle_id === vehicleFilter)
    if (statusFilter === 'all') return sorted
    if (statusFilter === 'due')
      return sorted.filter((r) => isDueSoon(r, vehicleKm[r.vehicle_id]))
    if (statusFilter === 'overdue') return sorted.filter(isOverdue)
    if (statusFilter === 'pending')
      return sorted.filter((r) => r.status === 'pending' && !isOverdue(r))
    return sorted.filter((r) => r.status === statusFilter)
  }, [rows, statusFilter, vehicleFilter, vehicleKm])

  const handleScanReminders = async () => {
    setScanning(true)
    try {
      const result = await scanReminders()
      message.success(
        `Đã quét: ${result.maintenance.length} lịch bảo trì + ${result.inspections.length} đăng kiểm tới hạn, gửi thành công ${result.sent}`,
      )
      load()
    } catch (e) {
      message.error(e.message)
    } finally {
      setScanning(false)
    }
  }

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({
      type: 'oil_change',
      status: 'pending',
      remind_days_before: reminderDefaults.remind_days_before,
      remind_km_before: reminderDefaults.remind_km_before,
    })
    setModalOpen(true)
  }

  const openEdit = (record) => {
    setEditing(record)
    form.setFieldsValue({
      vehicle_id: record.vehicle_id,
      driver_id: record.driver_id ?? null,
      vendor: record.vendor ?? '',
      type: record.type,
      scheduled_date: record.scheduled_date
        ? dayjs(record.scheduled_date)
        : null,
      status: record.status ?? 'pending',
      odometer: record.odometer ?? null,
      interval_km: record.interval_km ?? null,
      due_odometer_km: record.due_odometer_km ?? null,
      remind_days_before: record.remind_days_before ?? 7,
      remind_km_before: record.remind_km_before ?? 500,
      cost: record.cost ?? null,
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
        message.warning(
          NOTIFY_REASON[result.reason] || `Không gửi được: ${result.reason}`,
        )
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
    {
      title: 'Người phụ trách',
      dataIndex: 'driver_id',
      render: (id) => driverName[id] || '—',
    },
    { title: 'Gara thực hiện', dataIndex: 'vendor', render: (v) => v || '—' },
    { title: 'Hạng mục', dataIndex: 'type', render: typeLabel },
    {
      title: 'Ngày hẹn',
      dataIndex: 'scheduled_date',
      render: (d) => dayjs(d).format('DD/MM/YYYY'),
    },
    {
      title: 'Hẹn tới km',
      dataIndex: 'due_odometer_km',
      render: (v) => (v == null ? '—' : `${v.toLocaleString('vi-VN')} km`),
    },
    {
      title: 'Chi phí',
      dataIndex: 'cost',
      render: (v) => (v == null ? '—' : `${v.toLocaleString('vi-VN')}đ`),
    },
    {
      title: 'Trạng thái',
      key: 'status',
      render: (_, record) => (
        <JobStatusTag record={record} overdue={isOverdue(record)} />
      ),
    },
    {
      title: '',
      key: 'actions',
      width: 260,
      render: (_, record) => (
        <Space wrap>
          {record.status === 'awaiting_confirmation' ? (
            <Button
              size="small"
              type="primary"
              icon={<AuditOutlined />}
              onClick={() => setReviewId(record.id)}
            >
              Xem & xác nhận
            </Button>
          ) : (
            <Button
              size="small"
              icon={<BellOutlined />}
              loading={notifyingId === record.id}
              disabled={record.status === 'done'}
              onClick={() => handleNotify(record.id)}
            >
              Gửi nhắc
            </Button>
          )}
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
      <PageHeader
        title="Lịch bảo trì xe"
        subtitle="Lên lịch, theo dõi và nhắc bảo trì định kỳ cho đội xe"
        extra={
          <Space>
            <Button
              icon={<SyncOutlined />}
              loading={scanning}
              onClick={handleScanReminders}
            >
              Quét nhắc ngay
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
              Thêm lịch bảo trì
            </Button>
          </Space>
        }
      />

      {vehicleFilter && (
        <Alert
          className="mb-4"
          type="info"
          showIcon
          closable
          onClose={() => setSearchParams({})}
          message={
            <>
              Đang chỉ xem lịch sử bảo trì của xe{' '}
              <strong>{vehiclePlate[vehicleFilter] || vehicleFilter}</strong>.{' '}
              <a onClick={() => setSearchParams({})}>Xem tất cả xe</a>
            </>
          }
        />
      )}

      <Space className="mb-4" wrap>
        <Select
          value={statusFilter}
          onChange={setStatusFilter}
          style={{ width: 220 }}
          options={[
            { value: 'all', label: 'Tất cả' },
            { value: 'due', label: 'Sắp / đã tới hạn' },
            { value: 'awaiting_confirmation', label: 'Chờ xác nhận' },
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

      <JobReviewModal
        kind="maintenance"
        job={reviewTarget}
        title={reviewTarget ? typeLabel(reviewTarget.type).toLowerCase() : ''}
        plate={reviewTarget ? vehiclePlate[reviewTarget.vehicle_id] : ''}
        driverName={(id) => driverName[id]}
        onClose={() => setReviewId(null)}
        onDone={load}
      />

      <Modal
        open={modalOpen}
        title={editing ? 'Sửa lịch bảo trì' : 'Thêm lịch bảo trì'}
        onOk={handleSubmit}
        confirmLoading={saving}
        onCancel={() => setModalOpen(false)}
        okText="Lưu"
        cancelText="Huỷ"
        width={FULLSCREEN_MODAL.width}
        style={FULLSCREEN_MODAL.style}
        styles={FULLSCREEN_MODAL.styles}
        destroyOnHidden
      >
        <Form form={form} layout="vertical" style={FULLSCREEN_FORM_STYLE}>
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
          <div style={FORM_GRID}>
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
            <Form.Item name="vendor" label="Gara / đơn vị thực hiện">
              <Input placeholder="vd: Gara Thành Đạt" />
            </Form.Item>
          </div>

          <div style={FORM_GRID}>
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
              tooltip="Hệ thống tự nhắc trước khi tới ngày này (xem 'Báo trước mấy ngày' bên dưới)"
            >
              <DatePicker
                format="DD/MM/YYYY"
                style={{ width: '100%' }}
                placeholder="Chọn ngày"
              />
            </Form.Item>
          </div>

          <div style={FORM_GRID}>
            <Form.Item
              name="due_odometer_km"
              label="Hẹn tới km"
              tooltip="Km dự kiến tới hạn (vd: xe đang 49.700km, chu kỳ 5.000km/lần -> hẹn 54.700km). Bỏ trống nếu không nhắc theo km."
            >
              <InputNumber min={0} style={{ width: '100%' }} addonAfter="km" />
            </Form.Item>
            <Form.Item name="interval_km" label="Chu kỳ bảo trì">
              <InputNumber
                min={0}
                style={{ width: '100%' }}
                addonAfter="km"
                placeholder="vd: 5000"
              />
            </Form.Item>
            <Form.Item
              name="remind_days_before"
              label="Báo trước mấy ngày"
              rules={[{ required: true }]}
            >
              <InputNumber
                min={0}
                style={{ width: '100%' }}
                addonAfter="ngày"
              />
            </Form.Item>
            <Form.Item
              name="remind_km_before"
              label="Báo khi còn mấy km"
              rules={[{ required: true }]}
            >
              <InputNumber min={0} style={{ width: '100%' }} addonAfter="km" />
            </Form.Item>
            <Form.Item name="odometer" label="Số km lúc làm (khi xong)">
              <InputNumber min={0} style={{ width: '100%' }} addonAfter="km" />
            </Form.Item>
            <Form.Item name="cost" label="Chi phí">
              <InputNumber min={0} style={{ width: '100%' }} addonAfter="đ" />
            </Form.Item>
          </div>

          <Form.Item name="status" label="Trạng thái">
            <Select
              options={[
                { value: 'pending', label: 'Chờ tới hạn' },
                {
                  value: 'awaiting_confirmation',
                  label: 'Chờ xác nhận (tài xế đã báo xong)',
                  disabled: true,
                },
                { value: 'done', label: 'Đã xong' },
              ]}
            />
          </Form.Item>
          <Form.Item name="note" label="Ghi chú">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Maintenance
