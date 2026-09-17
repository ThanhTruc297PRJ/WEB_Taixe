import { Suspense, useCallback, useEffect, useState } from 'react'
import { App, Button, Layout, Spin } from 'antd'
import { WarningFilled } from '@ant-design/icons'
import { Outlet, useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import Sidebar from './Sidebar'
import Header from './Header'
import { useIncidentAlerts } from '../hooks/useIncidentAlerts'
import { playAlarm, unlockAudio } from '../services/alertSound'
import { DriversProvider } from '../contexts/DriversContext'

const { Content } = Layout

const SEVERITY_TEXT = {
  critical: 'Nghiêm trọng',
  high: 'Cảnh cáo',
  medium: 'Cảnh báo',
}

function DashboardLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [notificationsRefreshSignal, setNotificationsRefreshSignal] = useState(0)
  const { notification } = App.useApp()
  const navigate = useNavigate()

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
        ),
      })
    },
    [notification, navigate],
  )

  const { connected } = useIncidentAlerts(handleAlert)

  return (
    <DriversProvider>
      <Layout className="min-h-screen">
        <Sidebar collapsed={collapsed} />
        <Layout>
          <Header
            collapsed={collapsed}
            onToggle={() => setCollapsed((prev) => !prev)}
            wsConnected={connected}
            notificationsRefreshSignal={notificationsRefreshSignal}
          />
          <Content className="p-6">
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
