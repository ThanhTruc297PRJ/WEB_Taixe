import { useState } from 'react'
import { Button, Card, Form, Input, Typography, App, Spin } from 'antd'
import { LockOutlined, UserOutlined } from '@ant-design/icons'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/useAuth'

const { Title, Text } = Typography

const ERROR_MESSAGES = {
  'auth/invalid-email': 'Email không hợp lệ',
  'auth/user-disabled': 'Tài khoản đã bị vô hiệu hoá',
  'auth/user-not-found': 'Tài khoản không tồn tại',
  'auth/wrong-password': 'Sai mật khẩu',
  'auth/invalid-credential': 'Email hoặc mật khẩu không đúng',
  'auth/too-many-requests': 'Đăng nhập sai quá nhiều lần, vui lòng thử lại sau',
}

function Login() {
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()
  const { login, user, loading } = useAuth()
  const { message } = App.useApp()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Spin size="large" />
      </div>
    )
  }

  if (user) {
    return <Navigate to="/dashboard" replace />
  }

  const handleFinish = async ({ email, password }) => {
    setSubmitting(true)
    try {
      await login(email, password)
      message.success('Đăng nhập thành công')
      navigate('/dashboard', { replace: true })
    } catch (error) {
      message.error(
        ERROR_MESSAGES[error.code] || 'Đăng nhập thất bại, vui lòng thử lại',
      )
    } finally {
      setSubmitting(false)
    }
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
            name="email"
            label="Email"
            rules={[
              { required: true, message: 'Vui lòng nhập email' },
              { type: 'email', message: 'Email không hợp lệ' },
            ]}
          >
            <Input prefix={<UserOutlined />} placeholder="admin@example.com" />
          </Form.Item>
          <Form.Item
            name="password"
            label="Mật khẩu"
            rules={[{ required: true, message: 'Vui lòng nhập mật khẩu' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="••••••••" />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Button
              type="primary"
              htmlType="submit"
              block
              size="large"
              loading={submitting}
            >
              Đăng nhập
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default Login
