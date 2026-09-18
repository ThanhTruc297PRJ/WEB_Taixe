import dayjs from 'dayjs'

/** Khối nội dung ẩn (chỉ hiện khi in — xem rule @media print trong
 * src/index.css) dùng cho mọi nút "Xuất PDF" trong app. Bấm nút gọi
 * `window.print()`, trình duyệt tự cho chọn "Lưu dưới dạng PDF". */
export function PrintableReport({ title, subtitle, summary, columns, rows }) {
  return (
    <div id="printable-report" className="hidden">
      <div style={{ padding: 24, fontFamily: 'Arial, sans-serif', color: '#0f172a' }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>{title}</h1>
        {subtitle && (
          <p style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>{subtitle}</p>
        )}
        {summary && <div style={{ marginTop: 16 }}>{summary}</div>}
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            fontSize: 12,
            marginTop: 16,
          }}
        >
          <thead>
            <tr>
              {columns.map((c) => (
                <th
                  key={c.key}
                  style={{
                    border: '1px solid #cbd5e1',
                    padding: '6px 8px',
                    textAlign: 'left',
                    background: '#f1f5f9',
                  }}
                >
                  {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i}>
                {columns.map((c) => (
                  <td
                    key={c.key}
                    style={{ border: '1px solid #cbd5e1', padding: '6px 8px' }}
                  >
                    {c.value(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        <p style={{ marginTop: 16, fontSize: 11, color: '#94a3b8' }}>
          Xuất lúc {dayjs().format('DD/MM/YYYY HH:mm')}
        </p>
      </div>
    </div>
  )
}

export const triggerPrint = () => window.print()
