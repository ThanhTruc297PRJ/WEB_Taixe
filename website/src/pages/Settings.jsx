import { Card, Empty } from 'antd'
import PageHeader from '../components/PageHeader'

function Settings() {
  return (
    <div>
      <PageHeader title="Cài đặt" subtitle="Cấu hình hệ thống và tài khoản quản trị" />
      <Card>
        <Empty description="Chức năng đang được phát triển" />
      </Card>
    </div>
  )
}

export default Settings
