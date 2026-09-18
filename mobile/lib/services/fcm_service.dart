import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

import '../firebase_options.dart';
import 'alert_service.dart';
import 'driver_api.dart';

/// Đăng ký nhận FCM cho tài khoản tài xế đang dùng app + xử lý lệnh admin
/// đẩy xuống. Hiện chỉ có 1 loại lệnh: `type: play_alert_sound` (nút "Phát
/// loa cảnh báo" trên web admin) — tự phát âm thanh cảnh báo local qua
/// [AlertService], không cần tự vẽ UI thông báo riêng.
class FcmService {
  FcmService({DriverApi? driverApi}) : _driverApi = driverApi ?? DriverApi();

  final DriverApi _driverApi;

  /// Gọi 1 lần khi vào MainScreen (đã đăng nhập + hồ sơ active). Xin quyền
  /// thông báo, lấy token, đăng ký lên backend, lắng nghe tin nhắn khi app
  /// đang mở, và tự đăng ký lại nếu token đổi (Firebase thỉnh thoảng cấp
  /// token mới).
  Future<void> init(String driverId) async {
    try {
      await FirebaseMessaging.instance.requestPermission();

      final token = await FirebaseMessaging.instance.getToken();
      if (token != null) {
        await _driverApi.updateFcmToken(driverId, token);
      }

      FirebaseMessaging.instance.onTokenRefresh.listen((newToken) {
        _driverApi.updateFcmToken(driverId, newToken);
      });

      FirebaseMessaging.onMessage.listen(_handleMessage);
    } catch (_) {
      // Máy không hỗ trợ / bị chặn quyền thông báo -> bỏ qua, không chặn
      // luồng chính của app. Tài xế vẫn dùng được, chỉ là không nhận được
      // lệnh cảnh báo từ xa.
    }
  }

  void _handleMessage(RemoteMessage message) {
    if (message.data['type'] == 'play_alert_sound') {
      AlertService().playWarningAlert();
    }
  }
}

/// Handler cho tin nhắn tới khi app đang nền/tắt màn hình — Firebase yêu cầu
/// đây phải là hàm top-level (không phải method trong class), đăng ký 1 lần
/// trong main() TRƯỚC runApp().
@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  // Chạy trên isolate riêng, chưa có app Firebase nào khởi tạo sẵn.
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
  if (message.data['type'] == 'play_alert_sound') {
    await AlertService().playWarningAlert();
  }
}
