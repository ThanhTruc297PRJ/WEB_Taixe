import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  App,
  Button,
  Card,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Spin,
  Table,
  Tabs,
  Tag,
  Typography,
} from 'antd'
import {
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  PlusOutlined,
} from '@ant-design/icons'
import { formatDateTime } from '../utils/datetime'
import { collection, onSnapshot } from 'firebase/firestore'
import { db } from '../services/firebase'
import { apiPost } from '../services/api'
import {
  createKbDocument,
  deleteKbDocument,
  listKbDocuments,
  updateKbDocument,
} from '../services/kb'
import { deleteChatLog, listChatLogs } from '../services/assistant'
import { toDate } from '../utils/firestore'
import PageHeader from '../components/PageHeader'

const { Text, Paragraph } = Typography

const CATEGORY_META = {
  safety: { label: 'An toàn lái xe', color: 'green' },
  traffic_law: { label: 'Luật giao thông', color: 'blue' },
  vehicle_manual: { label: 'Cẩm nang xe', color: 'orange' },
}

const INTENT_META = {
  safety: { label: 'An toàn', color: 'green' },
  traffic_law: { label: 'Luật GT', color: 'blue' },
  maintenance: { label: 'Bảo trì', color: 'orange' },
  directions: { label: 'Hỏi đường', color: 'purple' },
  chitchat: { label: 'Trò chuyện', color: 'default' },
}

function IntentTag({ intent }) {
  if (!intent) return null
  const m = INTENT_META[intent] ?? { label: intent, color: 'default' }
  return <Tag color={m.color}>{m.label}</Tag>
}

function ChatTab() {
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
        {
          role: 'assistant',
          text: result.answer,
          sources: result.sources,
          intent: result.intent,
          llm: result.llm,
        },
      ])
    } catch (error) {
      message.error(error.message || 'Không gửi được câu hỏi, vui lòng thử lại')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="max-w-2xl">
      <div className="mb-4 flex max-h-[420px] flex-col gap-4 overflow-y-auto">
        {messages.length === 0 && (
          <Text type="secondary">
            Hỏi thử để kiểm tra trợ lý trả lời đúng theo cơ sở tri thức...
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
              className={`max-w-[80%] rounded-lg px-3 py-2 ${
                m.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-100'
              }`}
            >
              {m.role === 'assistant' && (m.intent || m.llm === false) && (
                <div className="mb-1 flex flex-wrap items-center gap-1">
                  <IntentTag intent={m.intent} />
                  {m.llm === false && (
                    <Tag color="warning">Chưa cấu hình LLM</Tag>
                  )}
                </div>
              )}
              <Paragraph
                className="!mb-0 whitespace-pre-wrap"
                style={{ color: m.role === 'user' ? '#fff' : undefined }}
              >
                {m.text}
              </Paragraph>
              {m.sources?.length > 0 && (
                <div className="mt-1 flex flex-wrap gap-1">
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
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleAsk}
          loading={loading}
        >
          Gửi
        </Button>
      </div>
    </Card>
  )
}

function KnowledgeBaseTab() {
  const { message } = App.useApp()
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(null) // null = đóng, {} = thêm mới
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm()

  const load = useCallback(async () => {
    setLoading(true)
    try {
      setDocs(await listKbDocuments())
    } catch (e) {
      message.error(e.message)
    } finally {
      setLoading(false)
    }
  }, [message])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- nạp danh sách 1 lần khi mở tab
    load()
  }, [load])

  const openCreate = () => {
    setEditing({})
    form.setFieldsValue({ title: '', content: '', category: 'safety' })
  }
  const openEdit = (record) => {
    setEditing(record)
    form.setFieldsValue({
      title: record.title,
      content: record.content,
      category: record.category ?? 'safety',
    })
  }

  const handleSave = async () => {
    let values
    try {
      values = await form.validateFields()
    } catch {
      return
    }
    setSaving(true)
    try {
      if (editing.id) {
        await updateKbDocument(editing.id, values)
        message.success('Đã cập nhật tài liệu')
      } else {
        await createKbDocument(values)
        message.success('Đã thêm tài liệu')
      }
      setEditing(null)
      load()
    } catch (e) {
      message.error(e.message)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id) => {
    try {
      await deleteKbDocument(id)
      message.success('Đã xoá tài liệu')
      load()
    } catch (e) {
      message.error(e.message)
    }
  }

  const columns = useMemo(
    () => [
      { title: 'STT', key: 'stt', width: 55, render: (_, __, i) => i + 1 },
      { title: 'Tài liệu', dataIndex: 'title' },
      {
        title: 'Nhóm',
        dataIndex: 'category',
        width: 150,
        render: (c) => {
          const m = CATEGORY_META[c] ?? CATEGORY_META.safety
          return <Tag color={m.color}>{m.label}</Tag>
        },
      },
      {
        title: 'Số đoạn',
        dataIndex: 'chunks',
        width: 100,
        align: 'center',
        render: (n) => <Tag>{n ?? 0}</Tag>,
      },
      {
        title: 'Cập nhật',
        dataIndex: 'updated_at',
        width: 160,
        render: (v) => <span className="whitespace-nowrap">{formatDateTime(v)}</span>,
      },
      {
        title: '',
        key: 'actions',
        width: 140,
        align: 'right',
        render: (_, record) => (
          <div className="flex justify-end gap-2">
            <Button size="small" onClick={() => openEdit(record)}>
              Sửa
            </Button>
            <Popconfirm
              title="Xoá tài liệu này khỏi cơ sở tri thức?"
              okText="Xoá"
              cancelText="Huỷ"
              onConfirm={() => handleDelete(record.id)}
            >
              <Button size="small" danger>
                Xoá
              </Button>
            </Popconfirm>
          </div>
        ),
      },
    ],
    [], // eslint-disable-line react-hooks/exhaustive-deps
  )

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <Text type="secondary" className="text-sm">
          Nội dung markdown. Trợ lý AI tách theo tiêu đề <code>##</code> và tìm
          đoạn liên quan để trả lời tài xế.
        </Text>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          Thêm tài liệu
        </Button>
      </div>

      <Card styles={{ body: { padding: 0 } }}>
        <Table
          rowKey="id"
          loading={loading}
          columns={columns}
          dataSource={docs}
          scroll={{ x: 'max-content' }}
          pagination={false}
          locale={{ emptyText: 'Chưa có tài liệu nào' }}
        />
      </Card>

      <Modal
        open={editing != null}
        title={editing?.id ? 'Sửa tài liệu' : 'Thêm tài liệu'}
        onOk={handleSave}
        confirmLoading={saving}
        onCancel={() => setEditing(null)}
        okText="Lưu"
        cancelText="Huỷ"
        width={680}
        destroyOnHidden
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="title"
            label="Tiêu đề"
            rules={[{ required: true, message: 'Nhập tiêu đề' }]}
          >
            <Input placeholder="Ví dụ: Quy trình xử lý buồn ngủ" />
          </Form.Item>
          <Form.Item name="category" label="Nhóm">
            <Select
              options={[
                { value: 'safety', label: 'An toàn lái xe' },
                { value: 'traffic_law', label: 'Luật giao thông' },
                { value: 'vehicle_manual', label: 'Cẩm nang xe' },
              ]}
            />
          </Form.Item>
          <Form.Item
            name="content"
            label="Nội dung (markdown)"
            rules={[{ required: true, message: 'Nhập nội dung' }]}
          >
            <Input.TextArea
              rows={14}
              placeholder={'## Dấu hiệu\n- ...\n\n## Khuyến nghị\n- ...'}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

function ChatLogsTab() {
  const { message } = App.useApp()
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)

  const apply = useCallback((list) => {
    list.sort((a, b) => {
      const ta = toDate(a.created_at)?.getTime() ?? 0
      const tb = toDate(b.created_at)?.getTime() ?? 0
      return tb - ta
    })
    setLogs(list)
    setLoading(false)
  }, [])

  useEffect(() => {
    const unsub = onSnapshot(
      collection(db, 'chat_logs'),
      (snap) => apply(snap.docs.map((d) => ({ id: d.id, ...d.data() }))),
      () => {
        listChatLogs()
          .then(apply)
          .catch((e) => {
            message.error(e.message)
            setLoading(false)
          })
      },
    )
    return unsub
  }, [apply, message])

  const handleDelete = async (id) => {
    try {
      await deleteChatLog(id)
      message.success('Đã xoá log')
    } catch (e) {
      message.error(e.message)
    }
  }

  const columns = [
    { title: 'STT', key: 'stt', width: 55, render: (_, __, i) => i + 1 },
    {
      title: 'Thời gian',
      dataIndex: 'created_at',
      width: 160,
      render: (v) => <span className="whitespace-nowrap">{formatDateTime(v)}</span>,
    },
    {
      title: 'Người hỏi',
      dataIndex: 'email',
      width: 190,
      render: (v, r) => v || r.uid || '—',
    },
    {
      title: 'Ý định',
      dataIndex: 'intent',
      width: 110,
      render: (v) => <IntentTag intent={v} />,
    },
    {
      title: 'Câu hỏi',
      dataIndex: 'question',
      render: (v) => <span className="font-medium text-slate-800">{v}</span>,
    },
    {
      title: 'Trả lời',
      dataIndex: 'answer',
      render: (v, r) => (
        <div>
          <Paragraph className="!mb-1 whitespace-pre-wrap text-slate-600">
            {v}
          </Paragraph>
          {r.sources?.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {r.sources.map((s) => (
                <Tag key={s} color="blue">
                  {s}
                </Tag>
              ))}
            </div>
          )}
        </div>
      ),
    },
    {
      title: '',
      key: 'actions',
      width: 70,
      align: 'right',
      render: (_, r) => (
        <Popconfirm
          title="Xoá log này?"
          okText="Xoá"
          cancelText="Huỷ"
          onConfirm={() => handleDelete(r.id)}
        >
          <Button size="small" danger>
            Xoá
          </Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <Card styles={{ body: { padding: 0 } }}>
      <Table
        rowKey="id"
        loading={loading}
        columns={columns}
        dataSource={logs}
        scroll={{ x: 'max-content' }}
        pagination={{ pageSize: 15, showSizeChanger: false, hideOnSinglePage: true }}
        locale={{ emptyText: 'Chưa có phiên trò chuyện nào' }}
      />
    </Card>
  )
}

function Assistant() {
  return (
    <div>
      <PageHeader
        title="Trợ lý AI"
        subtitle="Cấu hình cơ sở tri thức, kiểm thử câu trả lời và kiểm duyệt lịch sử chat"
      />
      <Tabs
        items={[
          {
            key: 'kb',
            label: 'Cơ sở tri thức',
            children: <KnowledgeBaseTab />,
          },
          {
            key: 'logs',
            label: 'Lịch sử chat',
            children: <ChatLogsTab />,
          },
          {
            key: 'chat',
            label: 'Hỏi đáp thử',
            children: <ChatTab />,
          },
        ]}
      />
    </div>
  )
}

export default Assistant
