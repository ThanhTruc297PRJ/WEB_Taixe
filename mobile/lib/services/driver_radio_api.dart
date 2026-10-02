import 'api_client.dart';

/// Kênh radio do admin quản lý trên web. App KHÔNG viết cứng danh sách kênh
/// nữa — admin thêm/tắt kênh thì tài xế thấy ngay lần mở màn hình kế tiếp.
class DriverRadioApi {
  DriverRadioApi({ApiClient? client}) : _c = client ?? ApiClient();
  final ApiClient _c;

  /// Chỉ trả các kênh đang bật, đã sắp theo thứ tự admin đặt.
  Future<List<Map<String, dynamic>>> stations() async {
    final j = await _c.get('/radio/stations');
    return (j as List).cast<Map<String, dynamic>>();
  }

  /// Báo backend là tài xế bấm phát. Ném [ApiException] (403) nếu kênh đã bị tắt.
  Future<void> registerPlay(String stationId) async {
    await _c.post('/radio/stations/$stationId/play', const {});
  }
}
