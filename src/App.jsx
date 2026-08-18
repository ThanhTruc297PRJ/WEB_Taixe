import { ConfigProvider, App as AntApp } from 'antd'
import { RouterProvider } from 'react-router-dom'
import router from './routes'

function App() {
  return (
    <ConfigProvider>
      <AntApp>
        <RouterProvider router={router} />
      </AntApp>
    </ConfigProvider>
  )
}

export default App
