import { ConfigProvider, App as AntApp } from 'antd'
import { RouterProvider } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import router from './routes'
import theme from './theme'

// Dấu * bắt buộc mặc định của AntD nằm TRƯỚC nhãn ("* Xe") — đổi ra SAU nhãn
// ("Xe *") cho toàn bộ form trong app, khớp cách đọc quen thuộc hơn.
const requiredMark = (label, { required }) => (
  <>
    {label}
    {required && (
      <span style={{ color: '#ff4d4f', marginInlineStart: 4 }}>*</span>
    )}
  </>
)

function App() {
  return (
    <ConfigProvider theme={theme} form={{ requiredMark }}>
      <AntApp>
        <AuthProvider>
          <RouterProvider router={router} />
        </AuthProvider>
      </AntApp>
    </ConfigProvider>
  )
}

export default App
