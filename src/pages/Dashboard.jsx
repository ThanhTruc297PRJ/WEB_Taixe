import { Card, Col, Row, Statistic } from 'antd'
import {
  CarOutlined,
  TeamOutlined,
  WarningOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'

function Dashboard() {
  return (
    <div>
      <h1 className="text-xl font-semibold text-gray-800 mb-4">Tổng quan</h1>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Tài xế đang hoạt động"
              value={128}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Chuyến đang chạy"
              value={42}
              prefix={<CarOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Cảnh báo hôm nay"
              value={3}
              valueStyle={{ color: '#cf1322' }}
              prefix={<WarningOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Hệ thống ổn định"
              value={100}
              suffix="%"
              valueStyle={{ color: '#3f8600' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
