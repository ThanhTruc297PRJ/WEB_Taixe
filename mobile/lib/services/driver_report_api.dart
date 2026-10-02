import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import 'api_client.dart';
import 'auth_service.dart';

/// Báo cáo tài xế tự gửi (xe hỏng, va quẹt...) + hotline cứu hộ của công ty.
/// Ảnh gửi qua backend (multipart), app KHÔNG ghi thẳng Firebase Storage.
class DriverReportApi {
  DriverReportApi({String? baseUrl, AuthService? auth, ApiClient? client})
    : baseUrl =
          baseUrl ??
          const String.fromEnvironment(
            'API_BASE_URL',
            defaultValue: 'http://10.0.2.2:8000',
          ),
      _auth = auth ?? AuthService(),
      _c = client ?? ApiClient();

  final String baseUrl;
  final AuthService _auth;
  final ApiClient _c;

  Future<void> submit({required String note, File? photo}) async {
    final token = await _auth.idToken();
    final req =
        http.MultipartRequest('POST', Uri.parse('$baseUrl/driver-reports/'))
          ..headers['Authorization'] = 'Bearer $token'
          ..fields['note'] = note;
    if (photo != null) {
      final isPng = photo.path.toLowerCase().endsWith('.png');
      req.files.add(
        await http.MultipartFile.fromPath(
          'photo',
          photo.path,
          contentType: http.MediaType('image', isPng ? 'png' : 'jpeg'),
        ),
      );
    }

    final res = await http.Response.fromStream(await req.send());
    if (res.statusCode < 200 || res.statusCode >= 300) {
      var detail = 'Gửi báo cáo thất bại (${res.statusCode})';
      try {
        final body = jsonDecode(utf8.decode(res.bodyBytes));
        if (body is Map && body['detail'] is String) detail = body['detail'];
      } catch (_) {}
      throw ApiException(res.statusCode, detail);
    }
  }

  /// Rỗng = admin chưa cài hotline trong trang Cài đặt web.
  Future<String> companyHotline() async {
    final j = await _c.get('/settings/contact');
    return ((j as Map<String, dynamic>)['company_hotline'] as String? ?? '')
        .trim();
  }
}
