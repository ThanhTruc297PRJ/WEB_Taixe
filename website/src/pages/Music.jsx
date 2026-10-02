import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Alert,
  App,
  Avatar,
  Card,
  Col,
  Empty,
  Input,
  List,
  Modal,
  Row,
  Segmented,
  Switch,
  Table,
  Tag,
  Tooltip,
} from 'antd'
import {
  CustomerServiceOutlined,
  SoundOutlined,
  StopOutlined,
  FlagOutlined,
  PlayCircleFilled,
  PauseCircleFilled,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import { useMusicRealtime } from '../hooks/useMusicRealtime'
import { useDrivers } from '../contexts/useDrivers'
import { getTrackReports, listTracks, toggleTrack } from '../services/music'

function Music() {
  const { message } = App.useApp()
  const { drivers } = useDrivers()
  const { tracks: live, loading, error } = useMusicRealtime()
  const [fallback, setFallback] = useState(null)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')
  const [disableTarget, setDisableTarget] = useState(null)
  const [reason, setReason] = useState('')
  const [playingId, setPlayingId] = useState(null)
  const audioRef = useRef(null)
  const [reportTarget, setReportTarget] = useState(null)
  const [reportDetails, setReportDetails] = useState([])
  const [reportLoading, setReportLoading] = useState(false)

  const driverName = useMemo(() => {
    const map = {}
    for (const d of drivers) map[d.id] = d.name
    return map
  }, [drivers])

  const openReportDetails = async (track) => {
    setReportTarget(track)
    setReportLoading(true)
    try {
      setReportDetails(await getTrackReports(track.id))
    } catch (e) {
      message.error(e.message)
      setReportDetails([])
    } finally {
      setReportLoading(false)
    }
  }

  useEffect(() => {
    const audio = new Audio()
    audio.addEventListener('ended', () => setPlayingId(null))
    audioRef.current = audio
    return () => {
      audio.pause()
      audio.src = ''
    }
  }, [])

  const togglePreview = (track) => {
    const audio = audioRef.current
    if (!audio || !track.preview_url) {
      message.warning('Bài này không có bản nghe thử')
      return
    }
    if (playingId === track.id) {
      audio.pause()
      setPlayingId(null)
      return
    }
    audio.src = track.preview_url
    audio.play().catch(() => message.error('Không phát được bản nghe thử'))
    setPlayingId(track.id)
  }

  useEffect(() => {
    if (!error) return
    message.warning('Không nghe được realtime — dùng dữ liệu tải một lần.')
    listTracks()
      .then(setFallback)
      .catch((e) => message.error(e.message))
  }, [error, message])

  const rows = useMemo(
    () => (error ? (fallback ?? []) : live),
    [error, fallback, live],
  )

  const stats = useMemo(
    () => ({
      total: rows.length,
      enabled: rows.filter((t) => t.enabled !== false).length,
      disabled: rows.filter((t) => t.enabled === false).length,
      reported: rows.filter((t) => t.reported).length,
    }),
    [rows],
  )

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return rows
      .filter((t) => {
        if (filter === 'enabled' && t.enabled === false) return false
        if (filter === 'disabled' && t.enabled !== false) return false
        if (filter === 'reported' && !t.reported) return false
        if (!q) return true
        return [t.title, t.artist].filter(Boolean).some((v) =>
          String(v).toLowerCase().includes(q),
        )
      })
      .sort((a, b) => {
        // Bị báo cáo lên đầu, rồi tới nghe nhiều nhất.
        if (!!b.reported !== !!a.reported) return b.reported ? 1 : -1
        return (b.play_count ?? 0) - (a.play_count ?? 0)
      })
  }, [rows, search, filter])

  const doToggle = async (track, enabled, why) => {
    try {
      await toggleTrack(track.id, enabled, why)
      message.success(enabled ? 'Đã bật lại bài hát' : 'Đã tắt bài hát')
    } catch (e) {
      message.error(e.message)
    }
  }

  const onSwitch = (track, next) => {
    if (next) {
      doToggle(track, true)
    } else {
      setDisableTarget(track)
      setReason('')
    }
  }

  const confirmDisable = async () => {
    await doToggle(disableTarget, false, reason.trim() || undefined)
    setDisableTarget(null)
  }

  const columns = [
    {
      title: 'Bài hát',
      dataIndex: 'title',
      render: (title, t) => {
        const isPlaying = playingId === t.id
        return (
          <div className="flex items-center gap-3">
            <Tooltip title={isPlaying ? 'Dừng nghe thử' : 'Nghe thử (30s)'}>
              <button
                type="button"
                onClick={() => togglePreview(t)}
                className="shrink-0 text-2xl text-blue-500 transition-colors hover:text-blue-600 disabled:text-slate-300"
                disabled={!t.preview_url}
              >
                {isPlaying ? <PauseCircleFilled /> : <PlayCircleFilled />}
              </button>
            </Tooltip>
            <Avatar
              shape="square"
              size={40}
              src={t.artwork_url}
              icon={<CustomerServiceOutlined />}
            />
            <div className="leading-tight">
              <div className="font-medium text-slate-800">
                {title}
                {t.explicit && (
                  <Tag
                    color="volcano"
                    bordered={false}
                    className="ml-2 rounded px-1 text-[10px]"
                  >
                    EXPLICIT
                  </Tag>
                )}
              </div>
              <div className="text-xs text-slate-400">{t.artist}</div>
            </div>
          </div>
        )
      },
    },
    {
      title: 'Lượt phát',
      dataIndex: 'play_count',
      width: 110,
      align: 'center',
      render: (v) => v ?? 0,
    },
    {
      title: 'Báo cáo',
      dataIndex: 'report_count',
      width: 110,
      align: 'center',
      render: (v, t) =>
        t.reported ? (
          <Tooltip title="Bấm để xem tài xế nào đã báo cáo">
            <Tag
              color="red"
              bordered={false}
              icon={<FlagOutlined />}
              onClick={() => openReportDetails(t)}
              className="cursor-pointer"
            >
              {v ?? 1}
            </Tag>
          </Tooltip>
        ) : (
          <span className="text-slate-300">—</span>
        ),
    },
    {
      title: 'Trạng thái',
      dataIndex: 'enabled',
      width: 150,
      render: (enabled, t) => {
        const on = enabled !== false
        return (
          <Tooltip title={!on ? t.disabled_reason || 'Đã tắt' : ''}>
            <span className="flex items-center gap-2">
              <Switch
                checked={on}
                size="small"
                onChange={(next) => onSwitch(t, next)}
              />
              <span className={on ? 'text-emerald-600' : 'text-slate-400'}>
                {on ? 'Cho nghe' : 'Đã tắt'}
              </span>
            </span>
          </Tooltip>
        )
      },
    },
  ]

  return (
    <div>
      <PageHeader
        title="Quản lý nhạc"
        subtitle="Tài xế tìm nhạc qua app; tắt bài nào thì tài xế không nghe được nữa"
      />

      {error && (
        <Alert
          className="mb-4"
          type="warning"
          showIcon
          message="Realtime chưa hoạt động"
          description="Trang đang hiển thị dữ liệu tải một lần, sẽ không tự cập nhật."
        />
      )}

      <Row gutter={[16, 16]} className="mb-4">
        <Col xs={12} lg={6}>
          <StatCard
            icon={<CustomerServiceOutlined />}
            label="Tổng bài hát"
            value={loading ? '—' : stats.total}
            tone="blue"
          />
        </Col>
        <Col xs={12} lg={6}>
          <StatCard
            icon={<SoundOutlined />}
            label="Đang cho nghe"
            value={loading ? '—' : stats.enabled}
            tone="green"
          />
        </Col>
        <Col xs={12} lg={6}>
          <StatCard
            icon={<StopOutlined />}
            label="Đã tắt"
            value={loading ? '—' : stats.disabled}
            tone="rose"
          />
        </Col>
        <Col xs={12} lg={6}>
          <StatCard
            icon={<FlagOutlined />}
            label="Bị báo cáo"
            value={loading ? '—' : stats.reported}
            tone="amber"
          />
        </Col>
      </Row>

      <Card styles={{ body: { padding: 16 } }} className="mb-4">
        <div className="flex flex-wrap items-center gap-3">
          <Input.Search
            allowClear
            placeholder="Tìm theo tên bài hát, ca sĩ"
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: 300 }}
          />
          <Segmented
            value={filter}
            onChange={setFilter}
            options={[
              { value: 'all', label: `Tất cả (${stats.total})` },
              { value: 'enabled', label: `Cho nghe (${stats.enabled})` },
              { value: 'disabled', label: `Đã tắt (${stats.disabled})` },
              { value: 'reported', label: `Bị báo cáo (${stats.reported})` },
            ]}
          />
        </div>
      </Card>

      <Card styles={{ body: { padding: 0 } }}>
        <Table
          rowKey="id"
          loading={loading && !error}
          columns={columns}
          dataSource={filtered}
          locale={{ emptyText: 'Chưa có bài hát nào — tài xế tìm nhạc trên app sẽ hiện ở đây' }}
          pagination={{ pageSize: 12, showSizeChanger: false, hideOnSinglePage: true }}
        />
      </Card>

      <Modal
        open={!!disableTarget}
        title={`Tắt bài: ${disableTarget?.title ?? ''}`}
        onOk={confirmDisable}
        onCancel={() => setDisableTarget(null)}
        okText="Tắt bài này"
        okButtonProps={{ danger: true }}
        cancelText="Huỷ"
        destroyOnHidden
      >
        <p className="mb-2 text-sm text-slate-500">
          Sau khi tắt, tài xế sẽ không tìm thấy và không phát được bài này. Lý do
          (không bắt buộc) chỉ hiển thị cho admin.
        </p>
        <Input.TextArea
          rows={3}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Ví dụ: Lời bài hát không phù hợp"
        />
      </Modal>

      <Modal
        open={!!reportTarget}
        title={`Tài xế đã báo cáo: ${reportTarget?.title ?? ''}`}
        onCancel={() => setReportTarget(null)}
        footer={null}
        destroyOnHidden
      >
        {!reportLoading && reportDetails.length === 0 && (reportTarget?.report_count ?? 0) > 0 && (
          <Alert
            className="mb-3"
            type="warning"
            showIcon
            message={`${reportTarget.report_count} lượt báo cáo không rõ tài xế`}
            description={
              <>
                Đây là báo cáo cũ từ trước khi hệ thống lưu chi tiết từng lượt (ai báo, lúc
                nào) — chỉ còn lại lý do gần nhất:{' '}
                <strong>{reportTarget.last_report_reason || 'Không có lý do'}</strong>. Các
                lượt báo cáo mới từ giờ sẽ hiện đầy đủ bên dưới.
              </>
            }
          />
        )}
        <List
          loading={reportLoading}
          dataSource={reportDetails}
          locale={{ emptyText: <Empty description="Chưa có lượt báo cáo mới nào" /> }}
          renderItem={(r) => (
            <List.Item>
              <div className="flex w-full items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-medium text-slate-700">
                    {driverName[r.driver_id] || r.driver_id || 'Không rõ tài xế'}
                  </div>
                  <div className="text-xs text-slate-400">
                    {r.reason || 'Không có lý do'}
                  </div>
                </div>
                <div className="shrink-0 text-xs text-slate-400">
                  {r.reported_at ? dayjs(r.reported_at).format('HH:mm DD/MM/YYYY') : ''}
                </div>
              </div>
            </List.Item>
          )}
        />
      </Modal>
    </div>
  )
}

export default Music
