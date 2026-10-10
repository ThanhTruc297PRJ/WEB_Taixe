import 'package:google_mlkit_face_mesh_detection/google_mlkit_face_mesh_detection.dart';

/// Nguồn hình cho giám sát buồn ngủ. Có 2 loại, xử lý phía sau giống hệt nhau
/// (cùng model, cùng bộ cộng điểm mệt mỏi):
///   - [CameraFrameBuffer]: camera trước của điện thoại.
///   - [NetworkFrameSource]: camera gắn trên xe phát qua mạng (demo: camera
///     laptop chạy scripts/laptop_camera_stream.py).
abstract class FrameSource {
  /// true = camera ngoài (không phải camera của điện thoại).
  bool get isExternal;

  Future<void> start({required void Function(InputImage image) onFrame});

  Future<void> switchCamera({required void Function(InputImage image) onFrame});

  /// Chụp 1 ảnh tĩnh JPEG, trả đường dẫn file tạm hoặc null.
  Future<String?> capturePhoto();

  /// Quay clip sự cố, trả đường dẫn file tạm (mp4 hoặc webm) hoặc null.
  Future<String?> recordClip(Duration duration);

  Future<void> resumeStream({required void Function(InputImage image) onFrame});

  Future<void> stop();
}
