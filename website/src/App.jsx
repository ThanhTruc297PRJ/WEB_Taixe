import { ConfigProvider, App as AntApp } from 'antd'
import { RouterProvider } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import router from './routes'
import theme from './theme'

function App() {
  return (
    <ConfigProvider theme={theme}>
      <AntApp>
        <AuthProvider>
          <RouterProvider router={router} />
        </AuthProvider>
      </AntApp>
    </ConfigProvider>
  )
}

export default App
