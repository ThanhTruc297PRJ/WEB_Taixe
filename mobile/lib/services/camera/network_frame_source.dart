import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:google_mlkit_face_mesh_detection/google_mlkit_face_mesh_detection.dart';
import 'package:http/http.dart' as http;

import 'frame_source.dart';

/// Camera gắn trên xe phát qua mạng (HTTP). App lấy khung hình mới nhất
/// ~6 lần/giây từ `<url>/snapshot.jpg`, đưa vào đúng pipeline như camera điện
/// thoại; khi báo động thì xin `<url>/clip?seconds=10` làm clip sự cố.
///
/// Demo: laptop chạy `service/scripts/laptop_camera_stream.py`, điện thoại
/// nhập đường dẫn script in ra (cùng WiFi). Máy ảo Android: http://10.0.2.2:8081.
class NetworkFrameSource implements FrameSource {
  NetworkFrameSource(String baseUrl) : baseUrl = normalize(baseUrl);

  final String baseUrl;

  /// Khung hình JPEG mới nhất — màn giám sát hiển thị làm khung xem trước.
  final ValueNotifier<Uint8List?> latestJpeg = ValueNotifier(null);

  /// Lỗi kết nối gần nhất (null = đang nhận hình bình thường).
  final ValueNotifier<String?> error = ValueNotifier(null);

  static const _pollInterval = Duration(milliseconds: 166);
  static const _requestTimeout = Duration(seconds: 2);
  final http.Client _client = http.Client();
  Timer? _timer;
  bool _busy = false;
  int _tick = 0;
  int _failures = 0;
  Directory? _dir;

  @override
  bool get isExternal => true;

  /// "192.168.1.5:8081" -> "http://192.168.1.5:8081", bỏ dấu / cuối.
  static String normalize(String url) {
    var u = url.trim();
    if (!u.startsWith('http://') && !u.startsWith('https://')) u = 'http://$u';
    while (u.endsWith('/')) {
      u = u.substring(0, u.length - 1);
    }
    return u;
  }

  /// Kiểm tra kết nối — trả mô tả ngắn (VD "640×480, 15 khung/giây") hoặc ném
  /// lỗi có thông báo dễ hiểu.
  static Future<String> check(String url) async {
    final base = normalize(url);
    try {
      final res = await http
          .get(Uri.parse('$base/health'))
          .timeout(const Duration(seconds: 4));
      if (res.statusCode != 200) throw 'Camera trả lỗi ${res.statusCode}';
      final j = jsonDecode(res.body) as Map<String, dynamic>;
      if (j['ok'] != true) throw 'Camera đã kết nối nhưng chưa có hình';
      return '${j['width']}×${j['height']}, ${j['fps']} khung/giây';
    } on TimeoutException {
      throw 'Không kết nối được $base — kiểm tra laptop đang chạy script và cùng WiFi với điện thoại';
    } on SocketException {
      throw 'Không kết nối được $base — kiểm tra địa chỉ IP và WiFi';
    } on FormatException {
      throw 'Đường dẫn này không phải luồng camera của hệ thống';
    }
  }

  @override
  Future<void> start({required void Function(InputImage image) onFrame}) async {
    await check(baseUrl);
    _dir ??= await Directory(
      '${Directory.systemTemp.path}/external_camera',
    ).create(recursive: true);
    _failures = 0;
    error.value = null;
    _timer?.cancel();
    _timer = Timer.periodic(_pollInterval, (_) => _poll(onFrame));
  }

  Future<void> _poll(void Function(InputImage image) onFrame) async {
    if (_busy) return;
    _busy = true;
    try {
      final res = await _client
          .get(Uri.parse('$baseUrl/snapshot.jpg'))
          .timeout(_requestTimeout);
      if (res.statusCode != 200 || res.bodyBytes.isEmpty) {
        throw 'HTTP ${res.statusCode}';
      }
      final bytes = res.bodyBytes;
      latestJpeg.value = bytes;
      // ML Kit đọc JPEG qua file; xoay vòng 3 file để file đang được phân
      // tích không bị ghi đè bởi khung kế tiếp.
      final file = File('${_dir!.path}/frame_${_tick++ % 3}.jpg');
      await file.writeAsBytes(bytes, flush: true);
      _failures = 0;
      if (error.value != null) error.value = null;
      onFrame(InputImage.fromFilePath(file.path));
    } catch (_) {
      _failures++;
      if (_failures >= 6) {
        error.value = 'Mất kết nối camera ngoài — đang thử lại…';
      }
    } finally {
      _busy = false;
    }
  }

  /// Camera ngoài cố định trên xe — không đổi được hướng.
  @override
  Future<void> switchCamera({
    required void Function(InputImage image) onFrame,
  }) async {}

  @override
  @override
  Future<String?> capturePhoto() async {
    try {
      final res = await _client
          .get(Uri.parse('$baseUrl/snapshot.jpg'))
          .timeout(_requestTimeout);
      if (res.statusCode != 200 || res.bodyBytes.isEmpty) return null;
      final file = File(
        '${(_dir ?? Directory.systemTemp).path}/photo_${DateTime.now().millisecondsSinceEpoch}.jpg',
      );
      await file.writeAsBytes(res.bodyBytes, flush: true);
      return file.path;
    } catch (_) {
      return null;
    }
  }

  @override
  Future<String?> recordClip(Duration duration) async {
    try {
      final res = await _client
          .get(Uri.parse('$baseUrl/clip?seconds=${duration.inSeconds}'))
          .timeout(duration + const Duration(seconds: 15));
      if (res.statusCode != 200 || res.bodyBytes.isEmpty) return null;
      final file = File(
        '${(_dir ?? Directory.systemTemp).path}/clip_${DateTime.now().millisecondsSinceEpoch}.webm',
      );
      await file.writeAsBytes(res.bodyBytes, flush: true);
      return file.path;
    } catch (_) {
      return null;
    }
  }

  /// Luồng không dừng khi quay clip nên không cần làm gì.
  @override
  Future<void> resumeStream({
    required void Function(InputImage image) onFrame,
  }) async {}

  @override
  Future<void> stop() async {
    _timer?.cancel();
    _timer = null;
    latestJpeg.value = null;
    error.value = null;
  }
}
