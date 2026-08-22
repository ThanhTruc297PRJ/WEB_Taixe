import { useState } from 'react'
import { Button, Card, Divider, Form, Input, Typography, App, Spin } from 'antd'
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
  'auth/popup-closed-by-user': 'Bạn đã đóng cửa sổ đăng nhập Google',
}

function GoogleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 48 48" aria-hidden="true">
      <path
        fill="#FFC107"
        d="M43.6 20.5H42V20H24v8h11.3c-1.6 4.7-6.1 8-11.3 8-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.5 6.1 29.5 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.7-.4-3.5z"
      />
      <path
        fill="#FF3D00"
        d="M6.3 14.7l6.6 4.8C14.6 15.9 18.9 13 24 13c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.5 6.1 29.5 4 24 4 16.3 4 9.6 8.3 6.3 14.7z"
      />
      <path
        fill="#4CAF50"
        d="M24 44c5.4 0 10.3-2.1 14-5.5l-6.5-5.5c-2 1.4-4.6 2.3-7.5 2.3-5.2 0-9.6-3.3-11.3-7.9l-6.5 5C9.5 39.6 16.2 44 24 44z"
      />
      <path
        fill="#1976D2"
        d="M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.2 4.2-4.1 5.6l6.5 5.5C41.4 36.1 44 30.5 44 24c0-1.3-.1-2.7-.4-3.5z"
      />
    </svg>
  )
}

function Login() {
  const [submitting, setSubmitting] = useState(false)
  const [googleSubmitting, setGoogleSubmitting] = useState(false)
  const navigate = useNavigate()
  const { login, loginWithGoogle, user, loading } = useAuth()
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

  const handleGoogleLogin = async () => {
    setGoogleSubmitting(true)
    try {
      await loginWithGoogle()
      message.success('Đăng nhập thành công')
      navigate('/dashboard', { replace: true })
    } catch (error) {
      message.error(
        ERROR_MESSAGES[error.code] || 'Đăng nhập Google thất bại, vui lòng thử lại',
      )
    } finally {
      setGoogleSubmitting(false)
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
        <Divider plain>
          <Text type="secondary" style={{ fontSize: 12 }}>
            hoặc
          </Text>
        </Divider>
        <Button
          block
          size="large"
          icon={<GoogleIcon />}
          loading={googleSubmitting}
          onClick={handleGoogleLogin}
        >
          Đăng nhập với Google
        </Button>
      </Card>
    </div>
  )
}

export default Login
