/** Xuất mảng dữ liệu ra file CSV, tải về ngay trên trình duyệt (không cần
 * backend). Thêm BOM (U+FEFF) để Excel mở tiếng Việt không bị lỗi font. */
export function exportCsv(filename, rows, columns) {
  const escape = (v) => {
    const s = String(v ?? '')
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
  }
  const header = columns.map((c) => escape(c.label)).join(',')
  const lines = rows.map((row) => columns.map((c) => escape(c.value(row))).join(','))
  const csv = [header, ...lines].join('\n')

  const bom = String.fromCharCode(0xfeff)
  const blob = new Blob([bom + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
