import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  App,
  Avatar,
  Button,
  Card,
  Descriptions,
  Empty,
  Form,
  Input,
  InputNumber,
  Popconfirm,
  Space,
  Table,
  Tabs,
  Tag,
} from 'antd'
import {
  CameraOutlined,
  MailOutlined,
  PlusOutlined,
  DownloadOutlined,
  PrinterOutlined,
  SaveOutlined,
} from '@ant-design/icons'
import { sendPasswordResetEmail, updateProfile } from 'firebase/auth'
import { ref, uploadBytes, getDownloadURL } from 'firebase/storage'
import dayjs from 'dayjs'
import PageHeader from '../components/PageHeader'
import { PrintableReport, triggerPrint } from '../components/PrintableReport'
import { auth, storage } from '../services/firebase'
import { useAuth } from '../contexts/useAuth'
import { initials, avatarColor } from '../utils/avatar'
import {
  getSettings,
  updateSettings,
  listAdmins,
  grantAdmin,
  revokeAdmin,
} from '../services/settings'
import { listMaintenance } from '../services/maintenance'
import { listInspections } from '../services/inspections'
import { listVehicles } from '../services/vehicles'
import { exportCsv } from '../utils/csv'

// ── Tab: Tài khoản ─────────────────────────────────────────────────────
const MAX_AVATAR_BYTES = 3 * 1024 * 1024

function AccountTab() {
  const { message } = App.useApp()
  const { user, refreshUser } = useAuth()
  const [sending, setSending] = useState(false)
  const [name, setName] = useState(user?.displayName || '')
  const [savingName, setSavingName] = useState(false)
  const [photoURL, setPhotoURL] = useState(user?.photoURL || null)
  const [uploadingPhoto, setUploadingPhoto] = useState(false)
  const fileInputRef = useRef(null)

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- đồng bộ ô nhập với user khi context nạp/đổi tài khoản
    setName(user?.displayName || '')
    setPhotoURL(user?.photoURL || null)
  }, [user])

  const handlePickPhoto = () => fileInputRef.current?.click()

  const handlePhotoChange = async (e) => {
    const file = e.target.files?.[0]
    e.target.value = '' // reset để chọn lại đúng file cũ vẫn kích hoạt onChange
    if (!file) return
    if (!file.type.startsWith('image/')) {
      message.error('Chỉ nhận file ảnh')
      return
    }
    if (file.size > MAX_AVATAR_BYTES) {
      message.error('Ảnh tối đa 3MB')
      return
    }
    setUploadingPhoto(true)
    try {
      const path = `admin_avatars/${auth.currentUser.uid}/${Date.now()}_${file.name}`
      const fileRef = ref(storage, path)
      await uploadBytes(fileRef, file)
      const url = await getDownloadURL(fileRef)
      await updateProfile(auth.currentUser, { photoURL: url })
      setPhotoURL(url)
      await refreshUser()
      message.success('Đã cập nhật ảnh đại diện')
    } catch (err) {
      message.error(err.message)
    } finally {
      setUploadingPhoto(false)
    }
  }

  const handleSendReset = async () => {
    if (!user?.email) return
    setSending(true)
    try {
      await sendPasswordResetEmail(auth, user.email)
      message.success(`Đã gửi email đặt lại mật khẩu tới ${user.email}`)
    } catch (e) {
      message.error(e.message)
    } finally {
      setSending(false)
    }
  }

  const handleSaveName = async () => {
    const trimmed = name.trim()
    setSavingName(true)
    try {
      await updateProfile(auth.currentUser, { displayName: trimmed || null })
      await refreshUser()
      message.success('Đã cập nhật tên hiển thị')
    } catch (e) {
      message.error(e.message)
    } finally {
      setSavingName(false)
    }
  }

  const displayLabel = name || user?.email
  const created = user?.metadata?.creationTime
    ? dayjs(user.metadata.creationTime).format('DD/MM/YYYY')
    : '—'
  const lastLogin = user?.metadata?.lastSignInTime
    ? dayjs(user.metadata.lastSignInTime).format('DD/MM/YYYY HH:mm')
    : '—'

  return (
    <Card>
      <div className="flex items-center gap-4">
        <div className="relative">
          <Avatar
            size={56}
            src={photoURL || undefined}
            style={photoURL ? undefined : { backgroundColor: avatarColor(user?.email) }}
          >
            {!photoURL && initials(displayLabel)}
          </Avatar>
          <button
            type="button"
            onClick={handlePickPhoto}
            disabled={uploadingPhoto}
            className="absolute -bottom-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full border-2 border-white bg-blue-600 text-white shadow"
          >
            <CameraOutlined style={{ fontSize: 11 }} spin={uploadingPhoto} />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handlePhotoChange}
          />
        </div>
        <div>
          <div className="text-base font-semibold text-slate-800">{displayLabel}</div>
          <div className="text-sm text-slate-400">{user?.email}</div>
        </div>
      </div>

      <div className="mt-6 max-w-sm">
        <div className="mb-1 text-sm font-medium text-slate-600">Tên hiển thị</div>
        <Space.Compact className="w-full">
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Chưa đặt tên"
          />
          <Button type="primary" loading={savingName} onClick={handleSaveName}>
            Lưu
          </Button>
        </Space.Compact>
      </div>

      <Descriptions column={1} size="small" bordered className="mt-6 max-w-sm">
        <Descriptions.Item label="Vai trò">Quản trị viên</Descriptions.Item>
        <Descriptions.Item label="Tạo tài khoản">{created}</Descriptions.Item>
        <Descriptions.Item label="Đăng nhập gần nhất">{lastLogin}</Descriptions.Item>
      </Descriptions>

      <div className="mt-6">
        <Button icon={<MailOutlined />} loading={sending} onClick={handleSendReset}>
          Gửi email đổi mật khẩu
        </Button>
        <p className="mt-2 text-xs text-slate-400">
          Hệ thống gửi link đặt lại mật khẩu tới email trên — bấm vào link để đặt mật khẩu mới.
        </p>
      </div>
    </Card>
  )
}

// ── Tab: Quản trị viên ─────────────────────────────────────────────────
function AdminsTab() {
  const { message } = App.useApp()
  const { user } = useAuth()
  const [admins, setAdmins] = useState([])
  const [loading, setLoading] = useState(true)
  const [email, setEmail] = useState('')
  const [adding, setAdding] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      setAdmins(await listAdmins())
    } catch (e) {
      message.error(e.message)
    } finally {
      setLoading(false)
    }
  }, [message])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- nạp danh sách 1 lần khi mở tab
    load()
  }, [load])

  const handleAdd = async () => {
    const trimmed = email.trim()
    if (!trimmed) return
    setAdding(true)
    try {
      await grantAdmin(trimmed)
      message.success(`Đã cấp quyền admin cho ${trimmed}`)
      setEmail('')
      load()
    } catch (e) {
      message.error(e.message)
    } finally {
      setAdding(false)
    }
  }

  const handleRevoke = async (uid) => {
    try {
      await revokeAdmin(uid)
      message.success('Đã thu hồi quyền admin')
      load()
    } catch (e) {
      message.error(e.message)
    }
  }

  return (
    <Card>
      <Space.Compact className="mb-4 w-full max-w-md">
        <Input
          placeholder="Nhập email tài khoản đã có sẵn trên hệ thống"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          onPressEnter={handleAdd}
        />
        <Button type="primary" icon={<PlusOutlined />} loading={adding} onClick={handleAdd}>
          Cấp quyền admin
        </Button>
      </Space.Compact>
      <p className="mb-4 text-xs text-slate-400">
        Email phải là tài khoản Firebase đã đăng nhập ít nhất 1 lần (VD từng đăng nhập app
        tài xế hoặc web) — chưa hỗ trợ tạo tài khoản mới từ đây.
      </p>
      <Table
        rowKey="uid"
        loading={loading}
        dataSource={admins}
        pagination={false}
        columns={[
          { title: 'Email', dataIndex: 'email' },
          {
            title: '',
            key: 'actions',
            width: 140,
            align: 'right',
            render: (_, record) =>
              record.uid === user?.uid ? (
                <Tag>Bạn</Tag>
              ) : (
                <Popconfirm
                  title="Thu hồi quyền admin của tài khoản này?"
                  okText="Thu hồi"
                  cancelText="Huỷ"
                  onConfirm={() => handleRevoke(record.uid)}
                >
                  <Button size="small" danger>
                    Thu hồi
                  </Button>
                </Popconfirm>
              ),
          },
        ]}
      />
    </Card>
  )
}

// ── Tab: Ngưỡng cảnh báo + Mặc định nhắc lịch (cùng dùng 1 API settings) ──
function ThresholdsTab({ settings, onSaved }) {
  const { message } = App.useApp()
  const [form] = Form.useForm()
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (settings) form.setFieldsValue(settings.violation_thresholds)
  }, [settings, form])

  const handleSave = async () => {
    const values = await form.validateFields()
    if (values.reminder >= values.warning || values.warning >= values.suspend) {
      message.error('Thứ tự phải là: Nhắc nhở < Cảnh cáo < Đình chỉ')
      return
    }
    setSaving(true)
    try {
      const next = await updateSettings({ violation_thresholds: values })
      onSaved(next)
      message.success('Đã lưu ngưỡng điểm vi phạm')
    } catch (e) {
      message.error(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card>
      <p className="mb-4 text-sm text-slate-500">
        Áp dụng cho thanh tổng điểm vi phạm ở trang Báo cáo sự cố và mức độ cảnh báo realtime
        gửi tới web admin.
      </p>
      <Form form={form} layout="vertical" className="max-w-sm">
        <Form.Item name="reminder" label="Nhắc nhở (từ bao nhiêu điểm)" rules={[{ required: true }]}>
          <InputNumber min={0} style={{ width: '100%' }} addonAfter="điểm" />
        </Form.Item>
        <Form.Item name="warning" label="Cảnh cáo (từ bao nhiêu điểm)" rules={[{ required: true }]}>
          <InputNumber min={0} style={{ width: '100%' }} addonAfter="điểm" />
        </Form.Item>
        <Form.Item name="suspend" label="Đình chỉ (từ bao nhiêu điểm)" rules={[{ required: true }]}>
          <InputNumber min={0} style={{ width: '100%' }} addonAfter="điểm" />
        </Form.Item>
        <Button type="primary" icon={<SaveOutlined />} loading={saving} onClick={handleSave}>
          Lưu ngưỡng
        </Button>
      </Form>
    </Card>
  )
}

function ReminderDefaultsTab({ settings, onSaved }) {
  const { message } = App.useApp()
  const [form] = Form.useForm()
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (settings) {
      form.setFieldsValue({
        maintenance_remind_days_before: settings.maintenance_defaults.remind_days_before,
        maintenance_remind_km_before: settings.maintenance_defaults.remind_km_before,
        inspection_remind_days_before: settings.inspection_defaults.remind_days_before,
      })
    }
  }, [settings, form])

  const handleSave = async () => {
    const values = await form.validateFields()
    setSaving(true)
    try {
      const next = await updateSettings({
        maintenance_defaults: {
          remind_days_before: values.maintenance_remind_days_before,
          remind_km_before: values.maintenance_remind_km_before,
        },
        inspection_defaults: {
          remind_days_before: values.inspection_remind_days_before,
        },
      })
      onSaved(next)
      message.success('Đã lưu mặc định nhắc lịch')
    } catch (e) {
      message.error(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card>
      <p className="mb-4 text-sm text-slate-500">
        Giá trị điền sẵn khi tạo lịch bảo trì / hồ sơ đăng kiểm mới — vẫn chỉnh được riêng
        cho từng bản ghi sau khi tạo.
      </p>
      <Form form={form} layout="vertical" className="max-w-sm">
        <Form.Item
          name="maintenance_remind_days_before"
          label="Bảo trì — báo trước mấy ngày"
          rules={[{ required: true }]}
        >
          <InputNumber min={0} style={{ width: '100%' }} addonAfter="ngày" />
        </Form.Item>
        <Form.Item
          name="maintenance_remind_km_before"
          label="Bảo trì — báo khi còn mấy km"
          rules={[{ required: true }]}
        >
          <InputNumber min={0} style={{ width: '100%' }} addonAfter="km" />
        </Form.Item>
        <Form.Item
          name="inspection_remind_days_before"
          label="Đăng kiểm — báo trước mấy ngày (tính từ hạn tem)"
          rules={[{ required: true }]}
        >
          <InputNumber min={0} style={{ width: '100%' }} addonAfter="ngày" />
        </Form.Item>
        <Button type="primary" icon={<SaveOutlined />} loading={saving} onClick={handleSave}>
          Lưu mặc định
        </Button>
      </Form>
    </Card>
  )
}

// ── Tab: Báo cáo chi phí ───────────────────────────────────────────────
function CostReportTab() {
  const { message } = App.useApp()
  const [maintenance, setMaintenance] = useState([])
  const [inspections, setInspections] = useState([])
  const [vehicles, setVehicles] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([listMaintenance(), listInspections(), listVehicles()])
      .then(([m, i, v]) => {
        setMaintenance(m)
        setInspections(i)
        setVehicles(v)
      })
      .catch((e) => message.error(e.message))
      .finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps -- chỉ tải 1 lần khi mở tab
  }, [])

  const vehiclePlate = useMemo(() => {
    const map = {}
    for (const v of vehicles) map[v.id] = v.plate_number
    return map
  }, [vehicles])

  const totals = useMemo(() => {
    const maintenanceCost = maintenance.reduce((s, m) => s + (m.cost || 0), 0)
    const inspectionFee = inspections.reduce((s, i) => s + (i.inspection_fee || 0), 0)
    const roadFee = inspections.reduce((s, i) => s + (i.road_fee || 0), 0)
    return {
      maintenanceCost,
      inspectionFee,
      roadFee,
      grandTotal: maintenanceCost + inspectionFee + roadFee,
    }
  }, [maintenance, inspections])

  const byVehicle = useMemo(() => {
    const map = {}
    const add = (vehicleId, amount) => {
      if (!vehicleId || !amount) return
      map[vehicleId] = (map[vehicleId] || 0) + amount
    }
    for (const m of maintenance) add(m.vehicle_id, m.cost || 0)
    for (const i of inspections) add(i.vehicle_id, (i.inspection_fee || 0) + (i.road_fee || 0))
    return Object.entries(map)
      .map(([vehicleId, total]) => ({ vehicleId, total }))
      .sort((a, b) => b.total - a.total)
  }, [maintenance, inspections])

  const money = (v) => `${(v || 0).toLocaleString('vi-VN')}đ`

  const reportRows = useMemo(
    () => [
      ...maintenance.map((m) => ({
        loai: 'Bảo trì',
        xe: vehiclePlate[m.vehicle_id] || m.vehicle_id,
        ngay: m.scheduled_date ? dayjs(m.scheduled_date).format('DD/MM/YYYY') : '',
        hangMuc: m.type || '',
        chiPhi: m.cost || 0,
      })),
      ...inspections.map((i) => ({
        loai: 'Đăng kiểm',
        xe: vehiclePlate[i.vehicle_id] || i.vehicle_id,
        ngay: i.old_sticker_expiry ? dayjs(i.old_sticker_expiry).format('DD/MM/YYYY') : '',
        hangMuc: 'Phí kiểm định + phí đường bộ',
        chiPhi: (i.inspection_fee || 0) + (i.road_fee || 0),
      })),
    ],
    [maintenance, inspections, vehiclePlate],
  )

  const reportColumns = [
    { key: 'loai', label: 'Loại', value: (r) => r.loai },
    { key: 'xe', label: 'Xe', value: (r) => r.xe },
    { key: 'ngay', label: 'Ngày', value: (r) => r.ngay },
    { key: 'hangMuc', label: 'Hạng mục', value: (r) => r.hangMuc },
    { key: 'chiPhi', label: 'Chi phí (đ)', value: (r) => money(r.chiPhi) },
  ]

  const handleExportCsv = () => {
    exportCsv(
      `bao-cao-chi-phi-${dayjs().format('YYYY-MM-DD')}.csv`,
      reportRows,
      reportColumns.map((c) => ({ label: c.label, value: (r) => c.value(r) })),
    )
  }

  if (loading) return <Card loading />

  const hasData = maintenance.length > 0 || inspections.length > 0

  return (
    <Card
      extra={
        <Space>
          <Button icon={<DownloadOutlined />} onClick={handleExportCsv} disabled={!hasData}>
            Xuất CSV
          </Button>
          <Button icon={<PrinterOutlined />} onClick={triggerPrint} disabled={!hasData}>
            Xuất PDF
          </Button>
        </Space>
      }
    >
      {!hasData ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="Chưa có dữ liệu chi phí bảo trì/đăng kiểm nào"
        />
      ) : (
        <>
          <Descriptions column={1} bordered size="small" className="mb-6">
            <Descriptions.Item label="Tổng chi phí bảo trì">
              {money(totals.maintenanceCost)}
            </Descriptions.Item>
            <Descriptions.Item label="Tổng phí kiểm định">
              {money(totals.inspectionFee)}
            </Descriptions.Item>
            <Descriptions.Item label="Tổng phí bảo trì đường bộ">
              {money(totals.roadFee)}
            </Descriptions.Item>
            <Descriptions.Item label={<strong>Tổng cộng</strong>}>
              <strong className="text-blue-600">{money(totals.grandTotal)}</strong>
            </Descriptions.Item>
          </Descriptions>

          <div className="mb-2 text-sm font-semibold text-slate-600">Theo từng xe</div>
          <Table
            size="small"
            rowKey="vehicleId"
            dataSource={byVehicle}
            pagination={{ pageSize: 10, showSizeChanger: false, hideOnSinglePage: true }}
            columns={[
              {
                title: 'Xe',
                dataIndex: 'vehicleId',
                render: (id) => vehiclePlate[id] || id,
              },
              {
                title: 'Tổng chi phí',
                dataIndex: 'total',
                align: 'right',
                render: money,
              },
            ]}
          />

          <PrintableReport
            title="Báo cáo chi phí bảo trì & đăng kiểm"
            subtitle={`Tổng cộng: ${money(totals.grandTotal)} (Bảo trì ${money(totals.maintenanceCost)} · Phí kiểm định ${money(totals.inspectionFee)} · Phí đường bộ ${money(totals.roadFee)})`}
            columns={reportColumns}
            rows={reportRows}
          />
        </>
      )}
    </Card>
  )
}

function Settings() {
  const { message } = App.useApp()
  const [settings, setSettings] = useState(null)

  useEffect(() => {
    getSettings()
      .then(setSettings)
      .catch((e) => message.error(e.message))
    // eslint-disable-next-line react-hooks/exhaustive-deps -- chỉ tải 1 lần khi mở trang
  }, [])

  return (
    <div>
      <PageHeader title="Cài đặt" subtitle="Cấu hình hệ thống và tài khoản quản trị" />
      <Tabs
        items={[
          { key: 'account', label: 'Tài khoản', children: <AccountTab /> },
          { key: 'admins', label: 'Quản trị viên', children: <AdminsTab /> },
          {
            key: 'thresholds',
            label: 'Ngưỡng cảnh báo',
            children: <ThresholdsTab settings={settings} onSaved={setSettings} />,
          },
          {
            key: 'reminders',
            label: 'Mặc định nhắc lịch',
            children: <ReminderDefaultsTab settings={settings} onSaved={setSettings} />,
          },
          { key: 'costs', label: 'Báo cáo chi phí', children: <CostReportTab /> },
        ]}
      />
    </div>
  )
}

export default Settings
