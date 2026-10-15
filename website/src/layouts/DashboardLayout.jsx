import { Suspense, useCallback, useEffect, useState } from 'react'
import { App, Button, Grid, Layout, Space, Spin } from 'antd'
import {
  AuditOutlined,
  MessageOutlined,
  SoundOutlined,
  WarningFilled,
} from '@ant-design/icons'
import { Outlet, useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import Sidebar from './Sidebar'
import Header from './Header'
import { useIncidentAlerts } from '../hooks/useIncidentAlerts'
import { playAlarm, unlockAudio } from '../services/alertSound'
import { sendAlertSound } from '../services/drivers'
import { DriversProvider } from '../contexts/DriversContext'

const { Content } = Layout

const SEVERITY_TEXT = {
  critical: 'Nghiêm trọng',
  high: 'Cảnh cáo',
  medium: 'Cảnh báo',
}

function DashboardLayout() {
  const screens = Grid.useBreakpoint()
  const isMobile = !screens.lg
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [notificationsRefreshSignal, setNotificationsRefreshSignal] = useState(0)
  const { notification, message } = App.useApp()
  const navigate = useNavigate()

  const handleAlertSound = useCallback(
    async (alert) => {
      if (!alert.driver_id) return
      try {
        const result = await sendAlertSound(alert.driver_id)
        if (result.sent) {
          message.success(`Đã gửi cảnh báo tới ${alert.driver_name ?? 'tài xế'}`)
        } else {
          message.warning(`Không gửi được: ${result.reason}`)
        }
      } catch (e) {
        message.error(e.message)
      }
    },
    [message],
  )

  // Mở khoá âm thanh khi người dùng tương tác lần đầu (trình duyệt chặn autoplay).
  useEffect(() => {
    const unlock = () => unlockAudio()
    window.addEventListener('pointerdown', unlock, { once: true })
    window.addEventListener('keydown', unlock, { once: true })
    return () => {
      window.removeEventListener('pointerdown', unlock)
      window.removeEventListener('keydown', unlock)
    }
  }, [])

  const handleAlert = useCallback(
    (alert) => {
      setNotificationsRefreshSignal((prev) => prev + 1)
      playAlarm(alert.severity)
      notification.error({
        message: `${SEVERITY_TEXT[alert.severity] ?? 'Cảnh báo'}: ${
          alert.message ?? 'Vi phạm an toàn'
        }`,
        description: `${alert.driver_name ?? alert.driver_id ?? 'Tài xế'} · ${dayjs().format(
          'HH:mm:ss',
        )} · +${alert.points ?? 0} điểm`,
        icon: <WarningFilled style={{ color: '#f5222d' }} />,
        duration: 0,
        key: alert.incident_id ?? undefined,
        btn: (
          <Space>
            <Button
              size="small"
              icon={<SoundOutlined />}
              onClick={() => handleAlertSound(alert)}
            >
              Phát loa cảnh báo
            </Button>
            <Button
              type="primary"
              danger
              size="small"
              onClick={() => {
                notification.destroy(alert.incident_id ?? undefined)
                navigate('/incidents')
              }}
            >
              Xem chi tiết
            </Button>
          </Space>
        ),
      })
    },
    [notification, navigate, handleAlertSound],
  )

  const handleDriverReport = useCallback(
    (report) => {
      setNotificationsRefreshSignal((prev) => prev + 1)
      notification.info({
        message: `Báo cáo mới từ ${report.driver_name ?? 'tài xế'}`,
        description: report.note || 'Đính kèm ảnh, không có mô tả',
        icon: <MessageOutlined style={{ color: '#1677ff' }} />,
        key: report.report_id ?? undefined,
        btn: (
          <Button
            type="primary"
            size="small"
            onClick={() => {
              notification.destroy(report.report_id ?? undefined)
              navigate('/driver-reports')
            }}
          >
            Xem
          </Button>
        ),
      })
    },
    [notification, navigate],
  )

  const handleJobSubmitted = useCallback(
    (job) => {
      setNotificationsRefreshSignal((prev) => prev + 1)
      const page = job.kind === 'inspection' ? '/inspections' : '/maintenance'
      const key = `job-${job.job_id}`
      notification.info({
        message: `${job.driver_name ?? 'Tài xế'} báo đã xong ${(job.title ?? '').toLowerCase()}`,
        description: `Xe ${job.plate_number ?? ''} — cần xem ảnh và xác nhận`,
        icon: <AuditOutlined style={{ color: '#9333ea' }} />,
        key,
        btn: (
          <Button
            type="primary"
            size="small"
            onClick={() => {
              notification.destroy(key)
              navigate(`${page}?review=${job.job_id}`)
            }}
          >
            Xem & xác nhận
          </Button>
        ),
      })
    },
    [notification, navigate],
  )

  const { connected } = useIncidentAlerts(
    handleAlert,
    handleDriverReport,
    handleJobSubmitted,
  )

  return (
    <DriversProvider>
      <Layout className="min-h-screen">
        <Sidebar
          collapsed={collapsed}
          isMobile={isMobile}
          mobileOpen={mobileOpen}
          onMobileClose={() => setMobileOpen(false)}
        />
        <Layout>
          <Header
            collapsed={collapsed}
            onToggle={() => isMobile ? setMobileOpen((prev) => !prev) : setCollapsed((prev) => !prev)}
            wsConnected={connected}
            notificationsRefreshSignal={notificationsRefreshSignal}
          />
          <Content className="p-3 sm:p-4 lg:p-6">
            <div className="mx-auto max-w-[1280px]">
              <Suspense
                fallback={
                  <div className="flex justify-center pt-24">
                    <Spin size="large" />
                  </div>
                }
              >
                <Outlet />
              </Suspense>
            </div>
          </Content>
        </Layout>
      </Layout>
    </DriversProvider>
  )
}

export default DashboardLayout
