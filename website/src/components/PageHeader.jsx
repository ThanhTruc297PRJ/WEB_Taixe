// Tiêu đề trang dùng chung: tên trang + mô tả ngắn + vùng nút thao tác bên phải.
function PageHeader({ title, subtitle, extra }) {
  return (
    <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 className="m-0 text-2xl font-bold tracking-tight text-slate-800">
          {title}
        </h1>
        {subtitle && (
          <p className="mt-1 mb-0 text-sm text-slate-500">{subtitle}</p>
        )}
      </div>
      {extra && <div className="flex flex-wrap items-center gap-2">{extra}</div>}
    </div>
  )
}

export default PageHeader
