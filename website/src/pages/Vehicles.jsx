import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  App,
  Button,
  Card,
  Col,
  Empty,
  Form,
  Input,
  InputNumber,
  Modal,
  Pagination,
  Popconfirm,
  Row,
  Select,
  Space,
  Tag,
} from 'antd'
import { PlusOutlined, ToolOutlined } from '@ant-design/icons'
import { useLocation, useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import { listDrivers } from '../services/drivers'
import { listMaintenance } from '../services/maintenance'
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

const STATUS_DOT = { active: 'bg-emerald-400', maintenance: 'bg-amber-400', inactive: 'bg-slate-300' }

const statusLabel = (value) =>
  STATUS_OPTIONS.find((o) => o.value === value)?.label ?? value

function Vehicles() {
  const { message } = App.useApp()
  const location = useLocation()
  const navigate = useNavigate()
  const [rows, setRows] = useState([])
  const [drivers, setDrivers] = useState([])
  const [maintenance, setMaintenance] = useState([])
  const [loading, setLoading] = useState(false)
  // Điền sẵn từ khoá khi điều hướng tới từ ô tìm nhanh trên Header.
  const [search, setSearch] = useState(location.state?.initialSearch || '')
  const [statusFilter, setStatusFilter] = useState('all')
  const [driverFilter, setDriverFilter] = useState('all')
  const [page, setPage] = useState(1)
  const PAGE_SIZE = 12
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm()

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [vehicleList, driverList, maintenanceList] = await Promise.all([
        listVehicles(),
        listDrivers(),
        listMaintenance(),
      ])
      setRows(vehicleList)
      setDrivers(driverList)
      setMaintenance(maintenanceList)
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

  // Lịch bảo trì GẦN NHẤT còn chờ tới hạn của mỗi xe — để hiện trên thẻ.
  const nextMaintenanceByVehicle = useMemo(() => {
    const map = {}
    for (const m of maintenance) {
      if (m.status !== 'pending' || !m.vehicle_id || !m.scheduled_date) continue
      const current = map[m.vehicle_id]
      if (!current || dayjs(m.scheduled_date).isBefore(dayjs(current.scheduled_date))) {
        map[m.vehicle_id] = m
      }
    }
    return map
  }, [maintenance])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return rows.filter((v) => {
      const status = v.status ?? 'active'
      if (statusFilter !== 'all' && status !== statusFilter) return false
      if (driverFilter === 'unassigned' && v.driver_id) return false
      if (
        driverFilter !== 'all' &&
        driverFilter !== 'unassigned' &&
        v.driver_id !== driverFilter
      )
        return false
      if (!q) return true
      return [v.plate_number, v.brand, v.model]
        .filter(Boolean)
        .some((x) => String(x).toLowerCase().includes(q))
    })
  }, [rows, search, statusFilter, driverFilter])

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

  return (
    <div>
      <PageHeader
        title="Danh mục xe"
        subtitle="Theo dõi tài xế phụ trách, số KM và lịch bảo trì định kỳ"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            Thêm phương tiện
          </Button>
        }
      />

      <Space className="mb-4" wrap>
        <Input.Search
          allowClear
          placeholder="Tìm theo biển số, hãng, dòng xe"
          defaultValue={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          style={{ width: 280 }}
        />
        <Select
          value={statusFilter}
          onChange={(v) => { setStatusFilter(v); setPage(1) }}
          style={{ width: 190 }}
          options={[
            { value: 'all', label: 'Tất cả trạng thái' },
            ...STATUS_OPTIONS,
          ]}
        />
        <Select
          value={driverFilter}
          onChange={(v) => { setDriverFilter(v); setPage(1) }}
          showSearch
          optionFilterProp="label"
          style={{ width: 220 }}
          options={[
            { value: 'all', label: 'Tất cả tài xế' },
            { value: 'unassigned', label: 'Chưa gán tài xế' },
            ...drivers.map((d) => ({ value: d.id, label: d.name })),
          ]}
        />
      </Space>

      <div style={{ minHeight: 700 }}>
      {!loading && filtered.length === 0 ? (
        <Card>
          <Empty description="Không tìm thấy xe nào" />
        </Card>
      ) : (
        <Row gutter={[16, 16]}>
          {filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE).map((record) => {
            const status = record.status ?? 'active'
            const nextMaintenance = nextMaintenanceByVehicle[record.id]
            const dueSoon =
              nextMaintenance &&
              dayjs(nextMaintenance.scheduled_date).diff(dayjs(), 'day') <= 7
            return (
              <Col key={record.id} xs={24} sm={12} lg={8} xl={6}>
                <Card loading={loading} className="h-full" styles={{ body: { padding: 18 } }}>
                  <div className="mb-1 flex items-center justify-between">
                    <Tag bordered={false} className="rounded-full px-2.5 py-0.5">
                      {record.plate_number}
                    </Tag>
                    <span
                      className={`h-2.5 w-2.5 rounded-full ${STATUS_DOT[status]}`}
                      title={statusLabel(status)}
                    />
                  </div>
                  <div className="text-base font-semibold text-slate-800">
                    {record.brand} {record.model}
                  </div>
                  <div className="mb-3 text-xs text-slate-400">{record.year || '—'}</div>

                  <div className="space-y-1.5 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Tài xế</span>
                      <span className="font-medium text-slate-700">
                        {driverName[record.driver_id] || 'Chưa phân công'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Số KM hiện tại</span>
                      <span className="font-medium text-slate-700">
                        {record.current_odometer_km == null
                          ? '—'
                          : `${record.current_odometer_km.toLocaleString('vi-VN')} km`}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Hạn bảo trì</span>
                      <span
                        className={`font-medium ${dueSoon ? 'text-amber-600' : 'text-slate-700'}`}
                      >
                        {nextMaintenance
                          ? dayjs(nextMaintenance.scheduled_date).format('DD/MM/YYYY')
                          : 'Chưa có lịch'}
                      </span>
                    </div>
                  </div>

                  <div className="mt-4 flex gap-2">
                    <Button
                      size="small"
                      icon={<ToolOutlined />}
                      className="flex-1"
                      onClick={() => navigate(`/maintenance?vehicle_id=${record.id}`)}
                    >
                      Lịch sử
                    </Button>
                    <Button size="small" type="primary" className="flex-1" onClick={() => openEdit(record)}>
                      Quản lý
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
                  </div>
                </Card>
              </Col>
            )
          })}
        </Row>
      )}
      </div>

      {filtered.length > PAGE_SIZE && (
        <div className="mt-6 flex justify-center">
          <Pagination
            current={page}
            pageSize={PAGE_SIZE}
            total={filtered.length}
            onChange={setPage}
            showTotal={(total) => `${total} xe`}
          />
        </div>
      )}

      <Modal
        open={modalOpen}
        title={editing ? 'Sửa xe' : 'Thêm xe'}
        onOk={handleSubmit}
        confirmLoading={saving}
        onCancel={() => setModalOpen(false)}
        okText="Lưu"
        cancelText="Huỷ"
        styles={{ body: { maxHeight: '70vh', overflowY: 'auto', paddingRight: 4 } }}
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
