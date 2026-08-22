# Chính sách chấp thuận (Consent) và quyền riêng tư

## Vì sao cần chấp thuận (consent)

Ứng dụng sử dụng camera để giám sát khuôn mặt tài xế trong lúc lái xe nhằm phát hiện sớm dấu hiệu buồn ngủ/mất tập trung. Đây là dữ liệu sinh trắc học nhạy cảm, vì vậy tài xế phải chủ động chấp thuận trước khi tính năng giám sát được kích hoạt.

## Loại consent trong hệ thống

- `camera_monitoring`: đồng ý cho phép camera phân tích khuôn mặt trong lúc lái xe
- `data_sharing`: đồng ý chia sẻ dữ liệu incident với admin/công ty quản lý đội xe
- `emergency_contact`: đồng ý cho hệ thống liên hệ người thân trong trường hợp khẩn cấp

## Quy trình

1. Lần đầu mở app, tài xế được yêu cầu xem và chấp thuận từng loại consent
2. App gọi `POST /consent` gửi `consent_type` và `accepted` kèm Firebase ID Token
3. Tài xế có thể xem lại trạng thái các consent đã chấp thuận qua `GET /consent`
4. Nếu tài xế từ chối `camera_monitoring`, tính năng giám sát buồn ngủ/mất tập trung sẽ không hoạt động — app chỉ ghi nhận chuyến đi (trip) thông thường

## Dữ liệu được lưu trữ

- Video/hình ảnh khuôn mặt **không được lưu trữ vĩnh viễn** — chỉ xử lý theo thời gian thực trên thiết bị (on-device), không upload lên server
- Chỉ metadata của incident (loại, thời điểm, mức độ tin cậy) được lưu lên Firestore, không kèm hình ảnh
