# Driver Monitoring Support System

Hệ thống giám sát an toàn tài xế cho doanh nghiệp vận tải: phát hiện buồn ngủ/mất
tập trung qua app mobile, quản lý đội xe + duyệt tài xế + xử lý sự cố qua web admin.

- `service/` — Backend FastAPI (Python)
- `website/` — Web admin (React + Vite)
- `mobile/` — App tài xế (Flutter)

## Yêu cầu trước khi chạy

- Python venv đã cài sẵn tại `D:\WEBTAIXE\venv`
- Node.js (cho `website/`)
- Flutter SDK + Android SDK (cho `mobile/`), máy ảo Android hoặc điện thoại thật
- File cấu hình Firebase (`.env`, `serviceAccountKey.json`...) đã có sẵn trong từng
  thư mục — không có sẵn thì hỏi người quản lý dự án, không tự tạo mới

## Cổng (port) dùng

| Cổng | Dịch vụ | Bắt buộc? |
|---|---|---|
| 8000 | Backend FastAPI | ✅ Luôn cần — cả web lẫn app mobile đều gọi vào đây |
| 5173 | Web admin (Vite dev server) | Chỉ cần nếu dùng web |
| 5554/5555 | Android Emulator | Chỉ cần nếu test mobile qua máy ảo (dùng điện thoại thật cắm USB thì khỏi cần) |

Firebase (Auth/Firestore/Storage) là dịch vụ đám mây của Google — không cần chạy gì
thêm ở máy, chỉ cần có Internet.

**Luôn chạy Backend trước tiên** — web admin và app mobile đều phụ thuộc vào nó.

## 1. Chạy Backend

```bash
cd D:\WEBTAIXE\driver_monitoring_support_system\service
D:\WEBTAIXE\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Thấy 2 dòng này là xong:

```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Để nguyên cửa sổ này chạy — đóng lại là web/app mất kết nối ngay.

## 2. Chạy Web Admin

Mở **cửa sổ terminal khác** (không dùng chung với Backend):

```bash
cd D:\WEBTAIXE\driver_monitoring_support_system\website
npm run dev
```

Thấy dòng `Local: http://localhost:5173/` là xong. Mở đúng link này trong trình
duyệt — backend chỉ cho phép CORS từ cổng **5173**, mở nhầm cổng khác (VD 5174 khi
Vite tự nhảy cổng vì 5173 đã bị chiếm) sẽ bị lỗi CORS.

## 3. Chạy App Mobile

### Trên máy ảo (emulator)

```bash
# Liệt kê máy ảo đã tạo
"%LOCALAPPDATA%\Android\Sdk\emulator\emulator.exe" -list-avds

# Khởi động máy ảo (dùng GPU thật cho ổn định, tránh crash/ANR)
"%LOCALAPPDATA%\Android\Sdk\emulator\emulator.exe" -avd Pixel_5 -gpu host

# Sau khi máy ảo boot xong, chạy app (trỏ về backend qua địa chỉ đặc biệt của emulator)
cd D:\WEBTAIXE\driver_monitoring_support_system\mobile
flutter run -d emulator-5554 --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

`10.0.2.2` là địa chỉ đặc biệt Android dùng để trỏ về `localhost` của máy tính đang
chạy emulator — không đổi được, không dùng `localhost` trực tiếp ở đây.

Lệnh trên chạy trong **cmd**. Giữ nguyên dấu ngoặc kép — tên người dùng Windows có
khoảng trắng (VD `C:\Users\Thanh Truc\...`) mà thiếu ngoặc kép sẽ báo lỗi
`'C:\Users\Thanh' is not recognized`. Nếu dùng PowerShell thì đổi `%LOCALAPPDATA%`
thành `$env:LOCALAPPDATA` và thêm `&` ở đầu lệnh.

### Trên điện thoại thật (cùng Wi-Fi với máy tính)

```bash
# Lấy IP LAN của máy tính
ipconfig
# tìm dòng IPv4 Address, dạng 192.168.x.x

cd D:\WEBTAIXE\driver_monitoring_support_system\mobile
flutter run --dart-define=API_BASE_URL=http://192.168.x.x:8000
```

Cần: điện thoại và máy tính cùng mạng Wi-Fi, và Windows Firewall không chặn cổng
8000 cho `python.exe`/`uvicorn`.

## Xử lý lỗi thường gặp

- **Web admin báo lỗi mạng / không tải được dữ liệu**: kiểm tra Backend còn chạy
  không (`netstat -ano | grep :8000` hoặc mở `http://localhost:8000/health`).
- **Lỗi CORS trên web** (`has been blocked by CORS policy`): đang mở nhầm cổng —
  kiểm tra thanh địa chỉ trình duyệt có đúng `localhost:5173` không.
- **App mobile báo `SocketException: Connection timed out`**: Backend chưa chạy,
  hoặc dùng sai địa chỉ (`10.0.2.2` cho emulator, IP LAN thật cho điện thoại thật).
- **Emulator bị crash/treo (ANR)**: khởi động lại với cờ `-gpu host` (dùng GPU thật
  của máy thay vì giả lập phần mềm, ổn định hơn nhiều).
- **Emulator không có Internet** (app báo `firebase_auth/network-request-failed`):
  khởi động lại emulator hoàn toàn (tắt hẳn tiến trình rồi mở lại), hoặc khởi động
  lại máy tính nếu vẫn không hết — đây là lỗi mạng ảo của Windows/emulator, không
  phải lỗi code.
