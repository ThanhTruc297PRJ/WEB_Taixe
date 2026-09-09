import { useState } from 'react'
import { Layout } from 'antd'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'

const { Content } = Layout

function DashboardLayout() {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <Layout className="min-h-screen">
      <Sidebar collapsed={collapsed} />
      <Layout>
        <Header
          collapsed={collapsed}
          onToggle={() => setCollapsed((prev) => !prev)}
        />
        <Content className="p-6">
          <div className="mx-auto max-w-[1280px]">
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}

export default DashboardLayout
