import 'api_client.dart';

/// Gọi các endpoint nhạc của backend (đã kiểm duyệt). App KHÔNG gọi thẳng
/// iTunes nữa — mọi tìm kiếm đi qua đây để admin kiểm soát nội dung.
class DriverMusicApi {
  DriverMusicApi({ApiClient? client}) : _c = client ?? ApiClient();
  final ApiClient _c;

  /// Trả danh sách bài hát đang được admin cho phép.
  Future<List<Map<String, dynamic>>> search(String query) async {
    final j = await _c.get('/music/search?q=${Uri.encodeQueryComponent(query)}');
    return (j as List).cast<Map<String, dynamic>>();
  }

  /// Báo backend là tài xế bấm phát. Ném [ApiException] (403) nếu bài đã bị tắt.
  Future<void> registerPlay(String trackId) async {
    await _c.post('/music/plays/$trackId', const {});
  }

  Future<void> report(String trackId, String? reason) async {
    await _c.post('/music/tracks/$trackId/report', {'reason': reason});
  }
}
