import { Button, Card, Space } from 'antd'
import { CheckCircleFilled } from '@ant-design/icons'

function App() {
  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center p-6">
      <Card className="w-full max-w-md shadow-lg rounded-2xl">
        <div className="text-center space-y-4">
          <CheckCircleFilled className="text-4xl text-emerald-500" />
          <h1 className="text-2xl font-bold text-gray-800">
            Driver Monitoring Admin Base
          </h1>
          <p className="text-sm text-gray-500">
            React.js + Vite + TailwindCSS + Ant Design đã sẵn sàng!
          </p>
          <Space size="middle">
            <Button type="primary" size="large">
              Bắt đầu dự án
            </Button>
          </Space>
        </div>
      </Card>
    </div>
  )
}

export default App
