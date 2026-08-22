# Phát hiện và xử lý mất tập trung khi lái xe

## Dấu hiệu hệ thống nhận diện

- **Nhìn lệch hướng lái xe**: hướng mặt/mắt lệch khỏi phía trước quá 30 độ trong hơn 2 giây liên tục
- **Sử dụng điện thoại**: phát hiện tay cầm vật thể dạng điện thoại gần mặt (mô hình TFLite phụ trợ)
- **Không phát hiện khuôn mặt**: camera không nhận diện được khuôn mặt tài xế quá 3 giây (có thể do cúi xuống, quay hẳn đi, hoặc che camera)

## Mức độ cảnh báo

Tương tự phân loại của cảnh báo buồn ngủ (nhẹ / mạnh / khẩn cấp), dựa trên `confidence` và thời lượng mất tập trung liên tục.

## Khuyến nghị xử lý cho tài xế

- Không sử dụng điện thoại khi xe đang di chuyển; nếu cần nghe/gọi, sử dụng loa ngoài hoặc dừng xe an toàn
- Đảm bảo camera giám sát không bị che khuất, gương chiếu hậu không cản tầm camera

## Khuyến nghị xử lý cho admin

- Incident loại `distraction` xảy ra dồn dập (trên 5 lần/chuyến) là dấu hiệu cần nhắc nhở trực tiếp tài xế, không chỉ dựa vào cảnh báo tự động
