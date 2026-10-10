// Popup thêm/sửa có form dài (bảo trì, đăng kiểm) mở cỡ lớn (~80% màn hình) —
// popup mặc định quá nhỏ phải cuộn trong khung, toàn màn hình thì quá trống.
// Dùng: <Modal width={FULLSCREEN_MODAL.width} style={FULLSCREEN_MODAL.style}
// styles={FULLSCREEN_MODAL.styles}>. Form dài hơn khung thì cuộn bên trong,
// nút Huỷ / Lưu luôn nằm ở đáy popup.
export const FULLSCREEN_MODAL = {
  width: '80vw',
  style: { top: '6vh', paddingBottom: 0 },
  styles: {
    container: {
      maxHeight: '86vh',
      display: 'flex',
      flexDirection: 'column',
      padding: '20px 28px',
    },
    header: { marginBottom: 16 },
    body: { flex: 1, minHeight: 0, overflowY: 'auto', paddingRight: 4 },
    footer: { marginTop: 16 },
  },
}

export const FULLSCREEN_FORM_STYLE = {}

// Class Tailwind "grid grid-cols-2" bị CSS của AntD đè trong Modal (render qua
// Portal) nên form chỉ còn 1 cột -> dùng style inline; tự xuống 1 cột khi màn hẹp.
export const FORM_GRID = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
  columnGap: 16,
}
