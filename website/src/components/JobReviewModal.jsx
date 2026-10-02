import { useState } from 'react'
import { Alert, App, Button, Descriptions, Image, Input, Modal, Space, Tag, Tooltip } from 'antd'
import dayjs from 'dayjs'
import { confirmJob, rejectJob } from '../services/vehicleJobs'

const AWAITING = 'awaiting_confirmation'

const money = (v) => (v == null ? '—' : `${Number(v).toLocaleString('vi-VN')}đ`)
const km = (v) => (v == null ? '—' : `${Number(v).toLocaleString('vi-VN')} km`)

/** Tag trạng thái dùng chung cho bảo trì / đăng kiểm. `overdueLabel` khác nhau
 * giữa 2 trang ("Quá hạn" / "Quá hạn tem"). */
export function JobStatusTag({ record, overdue, overdueLabel = 'Quá hạn' }) {
  if (record.status === 'done') return <Tag color="green">Đã xong</Tag>
  if (record.status === AWAITING) return <Tag color="purple">Chờ xác nhận</Tag>
  return (
    <Space size={4} wrap>
      {overdue ? <Tag color="red">{overdueLabel}</Tag> : <Tag color="blue">Chờ tới hạn</Tag>}
      {record.rejection && (
        <Tooltip title={`Lý do: ${record.rejection.reason}`}>
          <Tag color="orange">Đã trả lại</Tag>
        </Tooltip>
      )}
    </Space>
  )
}

/** Admin xem ảnh + số liệu tài xế gửi khi báo đã bảo trì / đăng kiểm xong,
 * rồi Xác nhận (lịch thành Đã xong) hoặc Trả lại kèm lý do (lịch về Chờ tới
 * hạn, tài xế nhận thông báo để gửi lại). */
function JobReviewModal({ kind, job, title, plate, driverName, onClose, onDone }) {
  const { message } = App.useApp()
  const [rejecting, setRejecting] = useState(false)
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(null) // 'confirm' | 'reject'

  const sub = job?.driver_submission
  const close = () => {
    setRejecting(false)
    setReason('')
    onClose()
  }

  const handleConfirm = async () => {
    setBusy('confirm')
    try {
      const res = await confirmJob(kind, job.id)
      message.success(
        res.next
          ? 'Đã xác nhận — đã tự tạo hồ sơ đăng kiểm kỳ tiếp theo'
          : 'Đã xác nhận hoàn tất',
      )
      close()
      onDone()
    } catch (e) {
      message.error(e.message)
    } finally {
      setBusy(null)
    }
  }

  const handleReject = async () => {
    const why = reason.trim()
    if (!why) {
      message.warning('Nhập lý do để tài xế biết cần gửi lại gì')
      return
    }
    setBusy('reject')
    try {
      await rejectJob(kind, job.id, why)
      message.success('Đã trả lại cho tài xế')
      close()
      onDone()
    } catch (e) {
      message.error(e.message)
    } finally {
      setBusy(null)
    }
  }

  const items = sub
    ? [
        { key: 'driver', label: 'Tài xế gửi', children: driverName(sub.submitted_by) || '—' },
        {
          key: 'at',
          label: 'Lúc',
          children: sub.submitted_at ? dayjs(sub.submitted_at).format('HH:mm DD/MM/YYYY') : '—',
        },
        { key: 'odo', label: 'Số km đồng hồ', children: km(sub.odometer) },
        ...(kind === 'maintenance'
          ? [{ key: 'cost', label: 'Chi phí', children: money(sub.cost) }]
          : [
              {
                key: 'result',
                label: 'Kết quả',
                children:
                  sub.result === 'passed' ? (
                    <Tag color="green">Đạt</Tag>
                  ) : (
                    <Tag color="red">Không đạt</Tag>
                  ),
              },
              {
                key: 'expiry',
                label: 'Hạn tem mới',
                children: sub.new_sticker_expiry
                  ? dayjs(sub.new_sticker_expiry).format('DD/MM/YYYY')
                  : '—',
              },
              { key: 'fee', label: 'Phí kiểm định', children: money(sub.inspection_fee) },
              { key: 'road', label: 'Phí đường bộ', children: money(sub.road_fee) },
            ]),
        { key: 'note', label: 'Ghi chú', children: sub.note || '—' },
      ]
    : []

  return (
    <Modal
      open={!!job}
      title={`Xác nhận ${title}: ${plate || ''}`}
      onCancel={close}
      width={720}
      destroyOnHidden
      footer={
        rejecting ? (
          <Space>
            <Button onClick={() => setRejecting(false)}>Quay lại</Button>
            <Button danger type="primary" loading={busy === 'reject'} onClick={handleReject}>
              Gửi trả lại
            </Button>
          </Space>
        ) : (
          <Space>
            <Button danger disabled={!sub} onClick={() => setRejecting(true)}>
              Trả lại
            </Button>
            <Button
              type="primary"
              disabled={!sub}
              loading={busy === 'confirm'}
              onClick={handleConfirm}
            >
              Xác nhận hoàn tất
            </Button>
          </Space>
        )
      }
    >
      {!sub ? (
        <Alert type="info" showIcon message="Lịch này không còn chờ xác nhận" />
      ) : (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16 }}>
          <div style={{ flex: '1 1 240px', minWidth: 0 }}>
            <Image
              src={sub.photo_url}
              alt="Ảnh hoá đơn / tem"
              style={{ width: '100%', maxHeight: 360, objectFit: 'contain', borderRadius: 8 }}
            />
            <div style={{ marginTop: 4, fontSize: 12, color: '#64748b' }}>
              Bấm vào ảnh để phóng to
            </div>
          </div>
          <div style={{ flex: '1 1 300px', minWidth: 0 }}>
            <Descriptions column={1} size="small" bordered items={items} />
          </div>
          {rejecting && (
            <div style={{ flexBasis: '100%' }}>
              <div style={{ marginBottom: 6, fontWeight: 500 }}>Lý do trả lại</div>
              <Input.TextArea
                autoFocus
                rows={3}
                maxLength={500}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Ví dụ: Ảnh hoá đơn bị mờ, chụp lại giúp mình"
              />
            </div>
          )}
        </div>
      )}
    </Modal>
  )
}

export default JobReviewModal
