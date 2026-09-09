import { useState } from 'react'
import { Button, Card, Input, Spin, Tag, Typography, App } from 'antd'
import { SendOutlined, RobotOutlined, UserOutlined } from '@ant-design/icons'
import { apiPost } from '../services/api'
import PageHeader from '../components/PageHeader'

const { Text, Paragraph } = Typography

function Assistant() {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const { message } = App.useApp()

  const handleAsk = async () => {
    const q = question.trim()
    if (!q || loading) return

    setMessages((prev) => [...prev, { role: 'user', text: q }])
    setQuestion('')
    setLoading(true)

    try {
      const result = await apiPost('/assistant/chat', { question: q })
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: result.answer, sources: result.sources },
      ])
    } catch (error) {
      message.error(error.message || 'Không gửi được câu hỏi, vui lòng thử lại')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="Trợ lý an toàn"
        subtitle="Hỏi nhanh về quy trình xử lý buồn ngủ, mất tập trung, chính sách consent"
      />
      <Card className="max-w-2xl">
        <div className="flex flex-col gap-4 mb-4 max-h-[420px] overflow-y-auto">
          {messages.length === 0 && (
            <Text type="secondary">
              Hỏi về quy trình xử lý buồn ngủ, mất tập trung, hoặc chính sách consent...
            </Text>
          )}
          {messages.map((m, i) => (
            <div
              key={i}
              className={`flex gap-2 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {m.role === 'assistant' && (
                <RobotOutlined className="mt-1 text-blue-500" />
              )}
              <div
                className={`rounded-lg px-3 py-2 max-w-[80%] ${
                  m.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-100'
                }`}
              >
                <Paragraph
                  className="!mb-0 whitespace-pre-wrap"
                  style={{ color: m.role === 'user' ? '#fff' : undefined }}
                >
                  {m.text}
                </Paragraph>
                {m.sources?.length > 0 && (
                  <div className="mt-1 flex gap-1 flex-wrap">
                    {m.sources.map((s) => (
                      <Tag key={s} color="blue">
                        {s}
                      </Tag>
                    ))}
                  </div>
                )}
              </div>
              {m.role === 'user' && <UserOutlined className="mt-1" />}
            </div>
          ))}
          {loading && <Spin size="small" />}
        </div>
        <div className="flex gap-2">
          <Input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onPressEnter={handleAsk}
            placeholder="Nhập câu hỏi..."
            disabled={loading}
          />
          <Button type="primary" icon={<SendOutlined />} onClick={handleAsk} loading={loading}>
            Gửi
          </Button>
        </div>
      </Card>
    </div>
  )
}

export default Assistant
