import 'dart:math';

import 'package:google_mlkit_face_mesh_detection/google_mlkit_face_mesh_detection.dart';

/// 1 mẫu tín hiệu thô cho 1 khung hình đã lấy mẫu (~6Hz, khớp
/// SAMPLE_RATE=5 trên video 30fps ở Notebook 1 lúc train).
class RawFrameSignal {
  const RawFrameSignal({
    required this.ear,
    required this.mar,
    required this.tilt,
    required this.earVel,
    required this.marVel,
  });

  final double ear;
  final double mar;
  final double tilt;
  final double earVel;
  final double marVel;
}

/// Tính EAR/MAR/HEAD_TILT/EAR_vel/MAR_vel từ landmark khuôn mặt — PHẢI khớp
/// chính xác công thức + chỉ số landmark dùng lúc train (Notebook 1), nếu
/// không model sẽ nhận input lệch phân phối và dự đoán sai mà không báo lỗi.
///
/// Landmark: MediaPipe FaceMesh, 468 điểm 3D. `google_mlkit_face_mesh_detection`
/// dùng chung topology 468 điểm với MediaPipe FaceMesh (theo tài liệu ML Kit),
/// nên đánh số chỉ số (362, 385, 387...) lấy nguyên từ code train là khớp.
///
/// LƯU Ý ĐƠN VỊ: `FaceMeshPoint.x/y` của ML Kit là toạ độ PIXEL trên ảnh gốc
/// (khác với MediaPipe Python solutions API vốn trả về toạ độ chuẩn hoá
/// [0,1] — đó là lý do Notebook 1 phải nhân thêm `* w`/`* h`). Ở đây dùng
/// thẳng x/y, KHÔNG nhân lại với width/height. Cần verify lại bằng cách log
/// range toạ độ thực tế (phải cỡ hàng trăm/nghìn, không phải 0..1) khi test
/// trên thiết bị thật lần đầu.
class LandmarkFeatureService {
  static const _leftEye = [362, 385, 387, 263, 373, 380];
  static const _rightEye = [33, 160, 158, 133, 153, 144];
  static const _mouth = [61, 39, 0, 269, 291, 405, 17, 181];
  static const _tiltRight = 454;
  static const _tiltLeft = 234;

  final FaceMeshDetector _detector = FaceMeshDetector(
    option: FaceMeshDetectorOptions.faceMesh,
  );

  double? _prevEar;
  double? _prevMar;

  Future<RawFrameSignal?> analyze(InputImage image) async {
    final meshes = await _detector.processImage(image);
    if (meshes.isEmpty) return null;

    final points = <int, FaceMeshPoint>{
      for (final p in meshes.first.points) p.index: p,
    };

    final earLeft = _eyeAspectRatio(points, _leftEye);
    final earRight = _eyeAspectRatio(points, _rightEye);
    final mar = _mouthAspectRatio(points, _mouth);
    if (earLeft == null || earRight == null || mar == null) return null;

    final ear = _round4((earLeft + earRight) / 2.0);
    final marRounded = _round4(mar);
    final tilt = _headTilt(points);

    final earVel = _prevEar == null ? 0.0 : _round4(ear - _prevEar!);
    final marVel = _prevMar == null ? 0.0 : _round4(marRounded - _prevMar!);
    _prevEar = ear;
    _prevMar = marRounded;

    return RawFrameSignal(ear: ear, mar: marRounded, tilt: tilt, earVel: earVel, marVel: marVel);
  }

  double? _eyeAspectRatio(Map<int, FaceMeshPoint> points, List<int> indices) {
    final pts = _lookup(points, indices);
    if (pts == null) return null;
    final a = _dist(pts[1], pts[5]);
    final b = _dist(pts[2], pts[4]);
    final c = _dist(pts[0], pts[3]);
    return c < 1e-6 ? null : (a + b) / (2.0 * c);
  }

  double? _mouthAspectRatio(Map<int, FaceMeshPoint> points, List<int> indices) {
    final pts = _lookup(points, indices);
    if (pts == null) return null;
    final a = _dist(pts[1], pts[7]);
    final b = _dist(pts[2], pts[6]);
    final c = _dist(pts[3], pts[5]);
    final d = _dist(pts[0], pts[4]);
    return d < 1e-6 ? null : (a + b + c) / (3.0 * d);
  }

  double _headTilt(Map<int, FaceMeshPoint> points) {
    final right = points[_tiltRight];
    final left = points[_tiltLeft];
    if (right == null || left == null) return 0.0;
    final dx = right.x - left.x;
    final dy = right.y - left.y;
    return _round4(atan2(dy, dx) * 180.0 / pi);
  }

  List<FaceMeshPoint>? _lookup(Map<int, FaceMeshPoint> points, List<int> indices) {
    final result = <FaceMeshPoint>[];
    for (final i in indices) {
      final p = points[i];
      if (p == null) return null;
      result.add(p);
    }
    return result;
  }

  double _dist(FaceMeshPoint a, FaceMeshPoint b) => sqrt(pow(a.x - b.x, 2) + pow(a.y - b.y, 2));

  double _round4(double v) => (v * 10000).round() / 10000;

  Future<void> dispose() => _detector.close();
}
