// Popup thêm/sửa có form dài (bảo trì, đăng kiểm) mở toàn màn hình — popup nhỏ
// phải cuộn trong khung, khó nhìn. Dùng: <Modal width="100vw" {...FULLSCREEN_MODAL}>
// và bọc form trong FULLSCREEN_FORM_STYLE để form không bị kéo dãn trên màn rộng.
const CONTENT_WIDTH = 880

export const FULLSCREEN_MODAL = {
  style: { top: 0, maxWidth: '100vw', margin: 0, paddingBottom: 0 },
  styles: {
    container: {
      minHeight: '100vh',
      borderRadius: 0,
      display: 'flex',
      flexDirection: 'column',
      padding: '20px 24px',
    },
    header: { maxWidth: CONTENT_WIDTH, width: '100%', margin: '0 auto 16px' },
    body: { flex: 1, overflowY: 'auto' },
    footer: { maxWidth: CONTENT_WIDTH, width: '100%', margin: '16px auto 0' },
  },
}

export const FULLSCREEN_FORM_STYLE = {
  maxWidth: CONTENT_WIDTH,
  margin: '0 auto',
}

// Class Tailwind "grid grid-cols-2" bị CSS của AntD đè trong Modal (render qua
// Portal) nên form chỉ còn 1 cột -> dùng style inline; tự xuống 1 cột khi màn hẹp.
export const FORM_GRID = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
  columnGap: 16,
}
