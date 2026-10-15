import { useCallback, useEffect, useMemo, useState } from 'react'
import { App, Button, Card, Image, Segmented, Table, Tag } from 'antd'
import { CheckOutlined, ReloadOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { formatDateTime } from '../utils/datetime'
import { useSearchParams } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import { useDrivers } from '../contexts/useDrivers'
import { listDriverReports, resolveDriverReport } from '../services/driverReports'

function DriverReports() {
  const { message } = App.useApp()
  const { drivers } = useDrivers()
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchParams, setSearchParams] = useSearchParams()
  const filter = searchParams.get('status') || 'new'
  const setFilter = (value) => setSearchParams(value === 'new' ? {} : { status: value })
  const [resolvingId, setResolvingId] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      setRows(await listDriverReports())
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

  const counts = useMemo(
    () => ({
      new: rows.filter((r) => r.status === 'new').length,
      resolved: rows.filter((r) => r.status === 'resolved').length,
    }),
    [rows],
  )

  const filtered = useMemo(
    () => (filter === 'all' ? rows : rows.filter((r) => r.status === filter)),
    [rows, filter],
  )

  const handleResolve = async (record) => {
    setResolvingId(record.id)
    try {
      const updated = await resolveDriverReport(record.id)
      setRows((prev) => prev.map((r) => (r.id === record.id ? { ...r, ...updated } : r)))
      message.success('Đã đánh dấu xử lý xong')
    } catch (e) {
      message.error(e.message)
    } finally {
      setResolvingId(null)
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
      title: 'Thời gian',
      dataIndex: 'created_at',
      width: 160,
      render: (v) => <span className="whitespace-nowrap">{formatDateTime(v)}</span>,
    },
    {
      title: 'Tài xế',
      dataIndex: 'driver_id',
      width: 170,
      render: (id) => driverName[id] || id,
    },
    {
      title: 'Mô tả',
      dataIndex: 'note',
      render: (v) => v || <span className="text-slate-400">(không có mô tả)</span>,
    },
    {
      title: 'Địa chỉ',
      key: 'address',
      width: 220,
      render: (_, r) => {
        if (!r.address && !r.latitude) return <span className="text-slate-300">—</span>
        const mapsUrl =
          r.latitude && r.longitude
            ? `https://www.google.com/maps?q=${r.latitude},${r.longitude}`
            : null
        return (
          <div className="text-xs">
            {r.address && <div className="text-slate-700">{r.address}</div>}
            {mapsUrl && (
              <a href={mapsUrl} target="_blank" rel="noreferrer" className="text-blue-500 hover:underline">
                Xem bản đồ ↗
              </a>
            )}
          </div>
        )
      },
    },
    {
      title: 'Ảnh',
      dataIndex: 'photo_url',
      width: 90,
      render: (url) =>
        url ? (
          <Image src={url} width={56} height={56} className="rounded object-cover" />
        ) : (
          <span className="text-slate-300">—</span>
        ),
    },
    {
      title: 'Trạng thái',
      dataIndex: 'status',
      width: 170,
      render: (status, r) =>
        status === 'resolved' ? (
          <div>
            <Tag color="green">Đã xử lý</Tag>
            {r.resolved_at && (
              <div className="mt-1 text-xs text-slate-400">
                {dayjs(r.resolved_at).format('HH:mm DD/MM')}
              </div>
            )}
          </div>
        ) : (
          <Tag color="orange">Chờ xử lý</Tag>
        ),
    },
    {
      title: '',
      key: 'actions',
      width: 140,
      render: (_, r) =>
        r.status === 'new' && (
          <Button
            size="small"
            type="primary"
            icon={<CheckOutlined />}
            loading={resolvingId === r.id}
            onClick={() => handleResolve(r)}
          >
            Đã xử lý
          </Button>
        ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="Báo cáo từ tài xế"
        subtitle="Tài xế tự gửi từ app (xe hỏng, va quẹt, sự cố dọc đường) — không tính điểm vi phạm"
        extra={
          <Button icon={<ReloadOutlined />} onClick={load} loading={loading}>
            Tải lại
          </Button>
        }
      />

      <Segmented
        className="mb-4"
        value={filter}
        onChange={setFilter}
        options={[
          { value: 'new', label: `Chờ xử lý (${counts.new})` },
          { value: 'resolved', label: `Đã xử lý (${counts.resolved})` },
          { value: 'all', label: `Tất cả (${rows.length})` },
        ]}
      />

      <Card styles={{ body: { padding: 0 } }}>
        <Table
          rowKey="id"
          loading={loading}
          columns={columns}
          dataSource={filtered}
          locale={{ emptyText: 'Chưa có báo cáo nào' }}
          pagination={{ pageSize: 10, showSizeChanger: false, hideOnSinglePage: true }}
        />
      </Card>
    </div>
  )
}

export default DriverReports
