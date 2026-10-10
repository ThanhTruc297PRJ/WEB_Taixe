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
import {
  AuditOutlined,
  BellOutlined,
  CheckCircleOutlined,
  PlusOutlined,
} from '@ant-design/icons'
import { useSearchParams } from 'react-router-dom'
import dayjs from 'dayjs'
import { formatDateTime } from '../utils/datetime'
import { listVehicles } from '../services/vehicles'
import { listDrivers } from '../services/drivers'
import { getSettings } from '../services/settings'
import {
  completeInspection,
  createInspection,
  deleteInspection,
  listInspections,
  notifyInspection,
  updateInspection,
} from '../services/inspections'
import PageHeader from '../components/PageHeader'
import JobReviewModal, { JobStatusTag } from '../components/JobReviewModal'
import {
  FORM_GRID,
  FULLSCREEN_FORM_STYLE,
  FULLSCREEN_MODAL,
} from '../config/fullscreenModal'

const NOTIFY_REASON = {
  driver_has_no_fcm_token:
    'Chưa gán người phụ trách hoặc chưa có thiết bị nhận thông báo',
  vehicle_not_found: 'Không tìm thấy xe',
  inspection_not_found: 'Không tìm thấy hồ sơ đăng kiểm',
}

const RESULT_META = {
  passed: { label: 'Đạt', color: 'green' },
  failed: { label: 'Không đạt', color: 'red' },
}

// Sắp / đã hết hạn tem: còn chờ và đã vào khoảng báo trước — cùng điều kiện với
// chuông thông báo và ô Đăng kiểm ở trang Tổng quan (inspection_service.list_upcoming).
const isDueSoon = (record) =>
  record.status === 'pending' &&
  !!record.old_sticker_expiry &&
  dayjs(record.old_sticker_expiry).diff(dayjs(), 'hour') / 24 <=
    (record.remind_days_before ?? 15)

// Quá hạn khi tem cũ đã hết hạn mà vẫn chưa đăng kiểm xong.
const isOverdue = (record) =>
  record.status === 'pending' &&
  dayjs(record.old_sticker_expiry).isBefore(dayjs(), 'day')

function Inspections() {
  const { message } = App.useApp()
  const [searchParams, setSearchParams] = useSearchParams()
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
  const [completeTarget, setCompleteTarget] = useState(null)
  const [completing, setCompleting] = useState(false)
  const [reminderDefaultDays, setReminderDefaultDays] = useState(15)
  const [form] = Form.useForm()
  const [completeForm] = Form.useForm()

  useEffect(() => {
    getSettings()
      .then((s) =>
        setReminderDefaultDays(s.inspection_defaults.remind_days_before),
      )
      .catch(() => {
        /* giữ mặc định cứng nếu tải cấu hình lỗi */
      })
  }, [])

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
    const sorted = [...rows].sort(
      (a, b) =>
        dayjs(a.old_sticker_expiry).valueOf() -
        dayjs(b.old_sticker_expiry).valueOf(),
    )
    if (statusFilter === 'all') return sorted
    if (statusFilter === 'due') return sorted.filter(isDueSoon)
    if (statusFilter === 'overdue') return sorted.filter(isOverdue)
    if (statusFilter === 'pending')
      return sorted.filter((r) => r.status === 'pending' && !isOverdue(r))
    return sorted.filter((r) => r.status === statusFilter)
  }, [rows, statusFilter])

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({ remind_days_before: reminderDefaultDays })
    setModalOpen(true)
  }

  const openEdit = (record) => {
    setEditing(record)
    form.setFieldsValue({
      vehicle_id: record.vehicle_id,
      driver_id: record.driver_id ?? null,
      station: record.station,
      appointment_at: record.appointment_at
        ? dayjs(record.appointment_at)
        : null,
      old_sticker_expiry: record.old_sticker_expiry
        ? dayjs(record.old_sticker_expiry)
        : null,
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
      appointment_at: values.appointment_at
        ? values.appointment_at.toISOString()
        : null,
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
    {
      title: 'STT',
      key: 'stt',
      width: 55,
      render: (_, __, index) => index + 1,
    },
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
    { title: 'Trạm đăng kiểm', dataIndex: 'station' },
    {
      title: 'Khung giờ hẹn',
      dataIndex: 'appointment_at',
      render: (d) => <span className="whitespace-nowrap">{formatDateTime(d, 'Chưa đặt lịch')}</span>,
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
        v ? (
          <Tag color={RESULT_META[v]?.color}>{RESULT_META[v]?.label}</Tag>
        ) : (
          '—'
        ),
    },
    {
      title: 'Trạng thái',
      key: 'status',
      render: (_, record) => (
        <JobStatusTag
          record={record}
          overdue={isOverdue(record)}
          overdueLabel="Quá hạn tem"
        />
      ),
    },
    {
      title: '',
      key: 'actions',
      width: 320,
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
          style={{ width: 220 }}
          options={[
            { value: 'all', label: 'Tất cả' },
            { value: 'due', label: 'Sắp / đã hết hạn tem' },
            { value: 'awaiting_confirmation', label: 'Chờ xác nhận' },
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

      <JobReviewModal
        kind="inspection"
        job={reviewTarget}
        title="đăng kiểm"
        plate={reviewTarget ? vehiclePlate[reviewTarget.vehicle_id] : ''}
        driverName={(id) => driverName[id]}
        onClose={() => setReviewId(null)}
        onDone={load}
      />

      <Modal
        open={modalOpen}
        title={editing ? 'Sửa hồ sơ đăng kiểm' : 'Thêm hồ sơ đăng kiểm'}
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
          <div style={FORM_GRID}>
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

          <div style={FORM_GRID}>
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
              <DatePicker
                format="DD/MM/YYYY"
                style={{ width: '100%' }}
                placeholder="Chọn ngày"
              />
            </Form.Item>
          </div>

          <Form.Item
            name="remind_days_before"
            label="Báo trước mấy ngày (tính từ hạn tem)"
            rules={[{ required: true }]}
          >
            <InputNumber min={0} style={{ width: '100%' }} addonAfter="ngày" />
          </Form.Item>

          <div style={FORM_GRID}>
            <Form.Item name="inspection_fee" label="Phí kiểm định">
              <InputNumber min={0} style={{ width: '100%' }} addonAfter="đ" />
            </Form.Item>
            <Form.Item name="road_fee" label="Phí bảo trì đường bộ">
              <InputNumber min={0} style={{ width: '100%' }} addonAfter="đ" />
            </Form.Item>
          </div>

          <Form.Item name="note" label="Ghi chú">
            <Input.TextArea rows={3} />
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
          <Form.Item
            name="result"
            label="Kết quả đăng kiểm"
            rules={[{ required: true }]}
          >
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
                  Xe cần sửa chữa rồi đặt lịch đăng kiểm lại — tạo hồ sơ mới sau
                  khi có lịch hẹn.
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
