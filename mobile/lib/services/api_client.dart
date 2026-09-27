import 'dart:convert';

import 'package:http/http.dart' as http;

import 'auth_service.dart';

class ApiException implements Exception {
  ApiException(this.statusCode, this.message);
  final int statusCode;
  final String message;
  @override
  String toString() => message;
}

/// HTTP client cho backend FastAPI. Tự đính `Authorization: Bearer <idToken>`.
///
/// trên emulator Android. Máy thật: truyền
/// `--dart-define=API_BASE_URL=http://<IP-máy>:8000`.
class ApiClient {
  ApiClient({String? baseUrl, AuthService? auth})
    : baseUrl =
          baseUrl ??
          const String.fromEnvironment(
            'API_BASE_URL',
            defaultValue: 'http://192.168.1.56:8000',
          ),
      _auth = auth ?? AuthService();

  final String baseUrl;
  final AuthService _auth;

  Future<Map<String, String>> _headers({bool forceRefresh = false}) async {
    final token = await _auth.idToken(forceRefresh: forceRefresh);
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  Future<dynamic> get(String path, {bool forceRefresh = false}) async {
    final r = await http.get(
      Uri.parse('$baseUrl$path'),
      headers: await _headers(forceRefresh: forceRefresh),
    );
    return _parse(r);
  }

  Future<dynamic> post(String path, Object body) async {
    final r = await http.post(
      Uri.parse('$baseUrl$path'),
      headers: await _headers(),
      body: jsonEncode(body),
    );
    return _parse(r);
  }

  Future<dynamic> put(String path, [Object? body]) async {
    final r = await http.put(
      Uri.parse('$baseUrl$path'),
      headers: await _headers(),
      body: body == null ? null : jsonEncode(body),
    );
    return _parse(r);
  }

  dynamic _parse(http.Response r) {
    dynamic data;
    if (r.body.isNotEmpty) {
      try {
        data = jsonDecode(r.body);
      } catch (_) {
        data = r.body;
      }
    }
    if (r.statusCode >= 200 && r.statusCode < 300) return data;
    final detail = (data is Map && data['detail'] != null)
        ? data['detail'].toString()
        : 'Lỗi ${r.statusCode}';
    throw ApiException(r.statusCode, detail);
  }
}
