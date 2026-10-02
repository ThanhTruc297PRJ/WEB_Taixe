import { useEffect, useMemo, useState } from 'react'
import { App, Button, Card, Descriptions, Empty, Space, Table } from 'antd'
import { DownloadOutlined, PrinterOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import PageHeader from '../components/PageHeader'
import { PrintableReport, triggerPrint } from '../components/PrintableReport'
import { listMaintenance } from '../services/maintenance'
import { listInspections } from '../services/inspections'
import { listVehicles } from '../services/vehicles'
import { exportCsv } from '../utils/csv'

function CostReport() {
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
    // eslint-disable-next-line react-hooks/exhaustive-deps -- chỉ tải 1 lần khi mở trang
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

  const hasData = maintenance.length > 0 || inspections.length > 0

  return (
    <div>
      <PageHeader
        title="Báo cáo chi phí"
        subtitle="Tổng hợp chi phí bảo trì & đăng kiểm theo từng xe"
      />

      <Card
        loading={loading}
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
    </div>
  )
}

export default CostReport
