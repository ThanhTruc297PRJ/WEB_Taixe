import 'package:flutter_foreground_task/flutter_foreground_task.dart';

/// TaskHandler (TASK-A01/SUB-03): chạy trong isolate riêng, giữ tiến trình
/// app sống + hiện notification liên tục trong lúc giám sát.
///
/// Lưu ý quan trọng: gói `camera` của Flutter gắn với texture của Activity ở
/// main isolate, nên việc đọc khung hình camera thực tế vẫn chạy trong
/// [CameraFrameBuffer] ở main isolate (xem MonitoringViewModel), KHÔNG chạy
/// bên trong handler này. Handler này đóng vai trò:
///   1. Giữ foreground service + notification để Android không kill app khi
///      màn hình tắt/app bị minimize.
///   2. Nhận trạng thái mới nhất từ main isolate qua [onReceiveData] và cập
///      nhật nội dung notification tương ứng.
/// Nếu sau này cần capture camera cả khi Activity không hiển thị, phải viết
/// thêm native code (CameraX chạy trực tiếp trong Android Service).
@pragma('vm:entry-point')
void monitoringTaskCallback() {
  FlutterForegroundTask.setTaskHandler(MonitoringTaskHandler());
}

class MonitoringTaskHandler extends TaskHandler {
  @override
  Future<void> onStart(DateTime timestamp, TaskStarter starter) async {
    FlutterForegroundTask.updateService(
      notificationTitle: 'Đang giám sát an toàn lái xe',
      notificationText: 'Trạng thái: bình thường',
    );
  }

  @override
  void onRepeatEvent(DateTime timestamp) {
    // Nhịp tim để giữ service alive; nội dung thật do onReceiveData cập nhật.
  }

  @override
  void onReceiveData(Object data) {
    if (data is String) {
      FlutterForegroundTask.updateService(
        notificationTitle: 'Đang giám sát an toàn lái xe',
        notificationText: data,
      );
    }
  }

  @override
  Future<void> onDestroy(DateTime timestamp) async {}
}
