import 'dart:io';

import 'package:http/http.dart' as http;

import 'api_client.dart';
import 'auth_service.dart';

/// Gửi sự cố (buồn ngủ / mất tập trung) kèm clip lên backend. Backend upload
/// clip lên Firebase Storage rồi tạo document — app KHÔNG ghi thẳng Storage.
class IncidentApi {
  IncidentApi({String? baseUrl, AuthService? auth})
      : baseUrl = baseUrl ??
            const String.fromEnvironment(
              'API_BASE_URL',
              defaultValue: 'http://10.0.2.2:8000',
            ),
        _auth = auth ?? AuthService();

  final String baseUrl;
  final AuthService _auth;

  Future<void> reportDrowsiness({
    required File clip,
    required DateTime detectedAt,
    double? confidence,
    String type = 'drowsiness',
  }) async {
    final token = await _auth.idToken();
    final req =
        http.MultipartRequest('POST', Uri.parse('$baseUrl/incidents/report'))
          ..headers['Authorization'] = 'Bearer $token'
          ..fields['type'] = type
          ..fields['detected_at'] = detectedAt.toUtc().toIso8601String()
          ..files.add(
            await http.MultipartFile.fromPath(
              'clip',
              clip.path,
              filename: 'clip.mp4',
            ),
          );
    if (confidence != null) {
      req.fields['confidence'] = confidence.toStringAsFixed(4);
    }

    final res = await http.Response.fromStream(await req.send());
    if (res.statusCode < 200 || res.statusCode >= 300) {
      throw ApiException(
        res.statusCode,
        'Gửi sự cố thất bại (${res.statusCode})',
      );
    }
  }
}
