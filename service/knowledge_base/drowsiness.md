# Phát hiện và xử lý buồn ngủ khi lái xe

## Dấu hiệu hệ thống nhận diện

Hệ thống giám sát qua camera (Google ML Kit Face Detection) phát hiện buồn ngủ dựa trên các chỉ số:

- **Nhắm mắt kéo dài**: mắt nhắm liên tục quá 1.5 giây (ngưỡng mặc định, có thể chỉnh trong Cài đặt)
- **Tần suất chớp mắt bất thường**: giảm mạnh so với mức trung bình của tài xế trong 5 phút gần nhất
- **Góc nghiêng đầu**: đầu gục xuống hoặc nghiêng quá 25 độ trong hơn 2 giây
- **Ngáp liên tục**: phát hiện từ 3 lần ngáp trở lên trong vòng 10 phút

## Mức độ cảnh báo

1. **Cảnh báo nhẹ** (confidence 0.5–0.7): rung điện thoại + âm thanh nhắc nhở
2. **Cảnh báo mạnh** (confidence 0.7–0.9): âm thanh lớn liên tục + thông báo đẩy (push notification) tới admin
3. **Cảnh báo khẩn cấp** (confidence > 0.9): ghi nhận sự cố (incident) vào hệ thống, gửi thông báo tới admin và (nếu cấu hình) người thân của tài xế

## Khuyến nghị xử lý cho tài xế

- Khi nhận cảnh báo, tài xế nên tấp vào lề đường an toàn trong vòng 5 phút
- Nghỉ ngơi tối thiểu 15–20 phút hoặc uống cà phê/nước tăng lực trước khi tiếp tục
- Nếu buồn ngủ tái diễn nhiều lần trong 1 chuyến đi, hệ thống khuyến nghị kết thúc chuyến và đổi tài xế

## Khuyến nghị xử lý cho admin

- Khi nhận được incident loại `drowsiness` với confidence cao, admin nên gọi điện xác nhận tình trạng tài xế trong vòng 10 phút
- Theo dõi lịch sử incident của từng tài xế tại trang **Sự cố** — nếu 1 tài xế có trên 3 incident buồn ngủ trong 1 tuần, cân nhắc yêu cầu khám sức khỏe hoặc điều chỉnh lịch chạy xe
