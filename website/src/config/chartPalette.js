// Bảng màu biểu đồ — đã chạy qua validate_palette (skill dataviz) trên nền trắng:
// 3 màu loại (categorical) phân biệt được cả với người mù màu (ΔE CVD ≥ 9).
// Màu xanh ngọc chỉ đạt 2.8:1 trên nền trắng nên biểu đồ luôn ghi số trực
// tiếp ở chú thích. Màu trạng thái dành riêng cho mức vi phạm, không dùng làm
// màu loại; chữ luôn dùng màu chữ (INK), không dùng màu cột.
export const SERIES = ['#2a78d6', '#eb6834', '#1baf7a']

export const STATUS = {
  good: '#0ca30c',
  warning: '#fab219',
  serious: '#ec835a',
  critical: '#d03b3b',
}

export const INK = { primary: '#0f172a', secondary: '#475569', muted: '#94a3b8' }
