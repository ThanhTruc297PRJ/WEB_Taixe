import { useEffect, useMemo, useState } from 'react'
import { Col, Row, Segmented } from 'antd'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import { ChartCard, DonutChart, RankBars, StackedColumns } from './DashboardCharts'
import { SERIES, STATUS } from '../config/chartPalette'
import { getSettings } from '../services/settings'
import { listMaintenance } from '../services/maintenance'
import { listInspections } from '../services/inspections'
import { toDate } from '../utils/firestore'
import { inspectionCostDate, maintenanceCostDate } from '../utils/costDates'
import { DEFAULT_THRESHOLDS, LEVEL_META, LEVELS, levelOf, levelRange, pointsByDriver } from '../utils/violationLevel'

const RANGES = [
  { value: 7, label: '7 ngày' },
  { value: 30, label: '30 ngày' },
  { value: 90, label: '90 ngày' },
]
const INCIDENT_TYPES = [
  { key: 'drowsiness', label: 'Buồn ngủ', color: SERIES[0] },
  { key: 'distraction', label: 'Mất tập trung', color: SERIES[1] },
]
const COST_SERIES = [
  { key: 'maintenance', label: 'Bảo trì', color: SERIES[0] },
  { key: 'inspection', label: 'Phí kiểm định', color: SERIES[1] },
  { key: 'road', label: 'Phí đường bộ', color: SERIES[2] },
]
const COST_MONTHS = 6

// "1,5 tr" / "450 N" — gọn cho trục và tooltip chi phí.
function compactMoney(v) {
  if (v >= 1e6) return `${(v / 1e6).toLocaleString('vi-VN', { maximumFractionDigits: 1 })} tr`
  if (v >= 1e3) return `${Math.round(v / 1e3).toLocaleString('vi-VN')} N`
  return `${v}đ`
}

const typeKey = (t) => (t === 'drowsiness' ? 'drowsiness' : 'distraction')

/** 5 biểu đồ trang Tổng quan: mức vi phạm tài xế, loại sự cố, top tài xế,
 * sự cố theo giờ, chi phí theo tháng. Bộ lọc thời gian áp cho 3 biểu đồ sự cố
 * (loại, top, theo giờ); mức vi phạm tính trên tổng điểm tích luỹ giống trang
 * Sự cố an toàn; chi phí luôn là 6 tháng gần nhất. */
function OverviewCharts({ incidents, drivers, loading = false }) {
  const navigate = useNavigate()
  const [days, setDays] = useState(30)
  const [thresholds, setThresholds] = useState(DEFAULT_THRESHOLDS)
  const [maintenance, setMaintenance] = useState([])
  const [inspections, setInspections] = useState([])
  const [costLoading, setCostLoading] = useState(true)

  useEffect(() => {
    getSettings()
      .then((s) => s.violation_thresholds && setThresholds(s.violation_thresholds))
      .catch(() => {
        /* giữ ngưỡng mặc định */
      })
    Promise.allSettled([
      listMaintenance().then(setMaintenance),
      listInspections().then(setInspections),
    ]).finally(() => setCostLoading(false)) // lỗi thì biểu đồ chi phí hiện rỗng
  }, [])

  const driverName = useMemo(() => {
    const map = {}
    for (const d of drivers) map[d.id] = d.name
    return map
  }, [drivers])

  // 1. Tài xế theo mức vi phạm (tổng điểm tích luỹ).
  const levels = useMemo(() => {
    const points = pointsByDriver(incidents)
    const count = { normal: 0, reminder: 0, warning: 0, suspend: 0 }
    for (const d of drivers) {
      if ((d.status ?? 'active') !== 'active') continue
      count[levelOf(points[d.id] || 0, thresholds)] += 1
    }
    const colors = {
      normal: STATUS.good,
      reminder: STATUS.warning,
      warning: STATUS.serious,
      suspend: STATUS.critical,
    }
    return LEVELS.map((key) => ({
      key,
      label: LEVEL_META[key].label,
      hint: levelRange(key, thresholds),
      value: count[key],
      color: colors[key],
    }))
  }, [incidents, drivers, thresholds])

  const inRange = useMemo(() => {
    const from = dayjs().subtract(days, 'day')
    return incidents.filter((i) => {
      const d = toDate(i.detected_at)
      return d && dayjs(d).isAfter(from)
    })
  }, [incidents, days])

  // 2. Loại sự cố.
  const byType = useMemo(
    () =>
      INCIDENT_TYPES.map((t) => ({
        ...t,
        value: inRange.filter((i) => typeKey(i.type) === t.key).length,
      })),
    [inRange],
  )

  // 3. Top 5 tài xế theo điểm vi phạm trong khoảng thời gian.
  const topDrivers = useMemo(() => {
    const agg = {}
    for (const i of inRange) {
      if (!i.driver_id) continue
      const a = (agg[i.driver_id] ??= { points: 0, count: 0 })
      a.points += i.points ?? 0
      a.count += 1
    }
    return Object.entries(agg)
      .filter(([, a]) => a.points > 0)
      .sort((a, b) => b[1].points - a[1].points)
      .slice(0, 5)
      .map(([id, a]) => ({
        key: id,
        label: driverName[id] || 'Tài xế đã xoá',
        sub: `${a.count} sự cố`,
        value: a.points,
        color: SERIES[0],
      }))
  }, [inRange, driverName])

  // 4. Sự cố theo giờ trong ngày (giờ máy người xem = giờ Việt Nam).
  const byHour = useMemo(() => {
    const rows = Array.from({ length: 24 }, (_, h) => ({
      label: `${h}h`,
      tipTitle: `${String(h).padStart(2, '0')}:00 – ${String(h).padStart(2, '0')}:59`,
      drowsiness: 0,
      distraction: 0,
    }))
    for (const i of inRange) {
      const d = toDate(i.detected_at)
      if (d) rows[d.getHours()][typeKey(i.type)] += 1
    }
    return rows
  }, [inRange])

  // 5. Chi phí 6 tháng gần nhất.
  const costByMonth = useMemo(() => {
    const start = dayjs().startOf('month').subtract(COST_MONTHS - 1, 'month')
    const rows = Array.from({ length: COST_MONTHS }, (_, i) => {
      const m = start.add(i, 'month')
      return {
        label: m.format('MM/YY'),
        month: m.format('YYYY-MM'),
        tipTitle: `Tháng ${m.format('MM/YYYY')} — bấm để xem chi tiết`,
        maintenance: 0,
        inspection: 0,
        road: 0,
      }
    })
    const add = (date, key, amount) => {
      if (!date || !amount) return
      const idx = dayjs(date).startOf('month').diff(start, 'month')
      if (idx >= 0 && idx < COST_MONTHS) rows[idx][key] += amount
    }
    for (const m of maintenance) {
      add(maintenanceCostDate(m), 'maintenance', m.cost || 0)
    }
    for (const i of inspections) {
      const date = inspectionCostDate(i)
      add(date, 'inspection', i.inspection_fee || 0)
      add(date, 'road', i.road_fee || 0)
    }
    return rows
  }, [maintenance, inspections])

  const rangeLabel = RANGES.find((r) => r.value === days)?.label

  return (
    <div className="mt-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h2 className="m-0 text-base font-semibold text-slate-800">Thống kê</h2>
        <Segmented value={days} onChange={setDays} options={RANGES} />
      </div>
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8}>
          <ChartCard title="Tài xế theo mức vi phạm" subtitle="Theo tổng điểm tích luỹ" loading={loading}>
            <DonutChart
              data={levels}
              centerLabel="tài xế"
              emptyText="Chưa có tài xế đang hoạt động"
              onSliceClick={(d) => navigate(`/drivers?level=${d.key}`)}
            />
          </ChartCard>
        </Col>
        <Col xs={24} lg={8}>
          <ChartCard title="Loại sự cố" subtitle={`${rangeLabel} gần nhất`} loading={loading}>
            <DonutChart
              data={byType}
              centerLabel="sự cố"
              emptyText={`Không có sự cố trong ${rangeLabel} gần nhất`}
              onSliceClick={(d) => navigate(`/incidents?type=${d.key}&days=${days}`)}
            />
          </ChartCard>
        </Col>
        <Col xs={24} lg={8}>
          <ChartCard title="Top tài xế nhiều điểm vi phạm" subtitle={`${rangeLabel} gần nhất`} loading={loading}>
            <RankBars
              rows={topDrivers}
              unit="Điểm vi phạm"
              emptyText={`Không tài xế nào bị trừ điểm trong ${rangeLabel} gần nhất`}
              onRowClick={(r) => navigate(`/incidents?driver=${r.key}&days=${days}`)}
            />
          </ChartCard>
        </Col>
        <Col xs={24} xl={14}>
          <ChartCard title="Sự cố theo giờ trong ngày" subtitle={`${rangeLabel} gần nhất — khung giờ dễ buồn ngủ`} loading={loading}>
            <StackedColumns
              rows={byHour}
              series={INCIDENT_TYPES}
              tickEvery={3}
              onColumnClick={(_, hour) => navigate(`/incidents?hour=${hour}&days=${days}`)}
              formatValue={(v) => Math.round(v).toLocaleString('vi-VN')}
              emptyText={`Không có sự cố trong ${rangeLabel} gần nhất`}
            />
          </ChartCard>
        </Col>
        <Col xs={24} xl={10}>
          <ChartCard title="Chi phí bảo trì & đăng kiểm" subtitle={`${COST_MONTHS} tháng gần nhất`} loading={costLoading}>
            <StackedColumns
              rows={costByMonth}
              series={COST_SERIES}
              formatValue={compactMoney}
              onColumnClick={(row) => navigate(`/costs?month=${row.month}`)}
              emptyText="Chưa có chi phí nào trong 6 tháng gần nhất"
            />
          </ChartCard>
        </Col>
      </Row>
    </div>
  )
}

export default OverviewCharts
