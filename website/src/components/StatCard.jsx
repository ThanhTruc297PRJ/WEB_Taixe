import { Card } from 'antd'

const TONES = {
  blue: 'bg-blue-50 text-blue-600',
  green: 'bg-emerald-50 text-emerald-600',
  rose: 'bg-rose-50 text-rose-600',
  amber: 'bg-amber-50 text-amber-600',
}

// Ô số liệu nhỏ đầu trang (icon + con số + nhãn) — dùng ở Quản lý nhạc/radio.
function StatCard({ icon, label, value, tone }) {
  return (
    <Card styles={{ body: { padding: 16 } }} className="h-full">
      <div className="flex items-center gap-3">
        <span
          className={`flex h-10 w-10 items-center justify-center rounded-xl text-lg ${TONES[tone]}`}
        >
          {icon}
        </span>
        <div>
          <div className="text-xl font-bold text-slate-800">{value}</div>
          <div className="text-xs text-slate-500">{label}</div>
        </div>
      </div>
    </Card>
  )
}

export default StatCard
