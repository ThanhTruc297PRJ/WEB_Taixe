import { Button, Card, Form, Input, Typography, App } from 'antd'
import { LockOutlined, UserOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const { Title, Text } = Typography

function Login() {
  const navigate = useNavigate()
  const { message } = App.useApp()

  const handleFinish = () => {
    localStorage.setItem('admin_token', 'true')
    message.success('Đăng nhập thành công')
    navigate('/dashboard', { replace: true })
  }

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center p-6">
      <Card className="w-full max-w-sm shadow-lg rounded-2xl">
        <Title level={3} style={{ textAlign: 'center', marginBottom: 4 }}>
          Driver Monitoring Admin
        </Title>
        <Text
          type="secondary"
          style={{ display: 'block', textAlign: 'center', marginBottom: 24 }}
        >
          Đăng nhập để tiếp tục
        </Text>
        <Form layout="vertical" onFinish={handleFinish}>
          <Form.Item
            name="username"
            label="Tài khoản"
            rules={[{ required: true, message: 'Vui lòng nhập tài khoản' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="admin" />
          </Form.Item>
          <Form.Item
            name="password"
            label="Mật khẩu"
            rules={[{ required: true, message: 'Vui lòng nhập mật khẩu' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="••••••••" />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Button type="primary" htmlType="submit" block size="large">
              Đăng nhập
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default Login
