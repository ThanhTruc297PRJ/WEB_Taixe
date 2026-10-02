import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import 'api_client.dart';
import 'auth_service.dart';

/// Một việc bảo trì hoặc đăng kiểm mà tài xế đang phụ trách.
class VehicleJob {
  VehicleJob({
    required this.kind,
    required this.id,
    required this.title,
    required this.status,
    this.plateNumber,
    this.currentOdometerKm,
    this.dueDate,
    this.dueOdometerKm,
    this.place,
    this.appointmentAt,
    this.rejectionReason,
  });

  final String kind; // 'maintenance' | 'inspection'
  final String id;
  final String title;
  final String status; // 'pending' | 'awaiting_confirmation'
  final String? plateNumber;
  final int? currentOdometerKm;
  final DateTime? dueDate;
  final int? dueOdometerKm;
  final String? place;
  final DateTime? appointmentAt;
  final String? rejectionReason;

  bool get isInspection => kind == 'inspection';
  bool get isAwaiting => status == 'awaiting_confirmation';

  static DateTime? _date(dynamic v) =>
      v is String ? DateTime.tryParse(v)?.toLocal() : null;

  factory VehicleJob.fromJson(Map<String, dynamic> j) => VehicleJob(
    kind: j['kind'] as String,
    id: j['id'] as String,
    title: j['title'] as String? ?? '',
    status: j['status'] as String? ?? 'pending',
    plateNumber: j['plate_number'] as String?,
    currentOdometerKm: (j['current_odometer_km'] as num?)?.toInt(),
    dueDate: _date(j['due_date']),
    dueOdometerKm: (j['due_odometer_km'] as num?)?.toInt(),
    place: j['place'] as String?,
    appointmentAt: _date(j['appointment_at']),
    rejectionReason: (j['rejection'] as Map?)?['reason'] as String?,
  );
}

/// Danh sách bảo trì / đăng kiểm của tài xế + gửi báo cáo "đã làm xong" (ảnh
/// hoá đơn/tem, số km, chi phí). Quản lý xác nhận trên web thì lịch mới xong.
class VehicleJobApi {
  VehicleJobApi({String? baseUrl, AuthService? auth, ApiClient? client})
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

  Future<List<VehicleJob>> mine() async {
    final j = await _c.get('/vehicle-jobs/mine');
    return (j as List)
        .cast<Map<String, dynamic>>()
        .map(VehicleJob.fromJson)
        .toList();
  }

  Future<void> submit({
    required VehicleJob job,
    required File photo,
    required int odometer,
    String note = '',
    double? cost,
    double? inspectionFee,
    double? roadFee,
    String? result,
    DateTime? newStickerExpiry,
  }) async {
    final token = await _auth.idToken();
    final req =
        http.MultipartRequest(
            'POST',
            Uri.parse('$baseUrl/vehicle-jobs/${job.kind}/${job.id}/submit'),
          )
          ..headers['Authorization'] = 'Bearer $token'
          ..fields['odometer'] = '$odometer'
          ..fields['note'] = note;
    if (cost != null) req.fields['cost'] = '$cost';
    if (inspectionFee != null) req.fields['inspection_fee'] = '$inspectionFee';
    if (roadFee != null) req.fields['road_fee'] = '$roadFee';
    if (result != null) req.fields['result'] = result;
    if (newStickerExpiry != null) {
      // Giữa ngày giờ địa phương -> đổi sang UTC không bị lùi sang ngày hôm trước.
      final d = newStickerExpiry;
      req.fields['new_sticker_expiry'] = DateTime(
        d.year,
        d.month,
        d.day,
        12,
      ).toUtc().toIso8601String();
    }
    final isPng = photo.path.toLowerCase().endsWith('.png');
    req.files.add(
      await http.MultipartFile.fromPath(
        'photo',
        photo.path,
        contentType: http.MediaType('image', isPng ? 'png' : 'jpeg'),
      ),
    );

    final res = await http.Response.fromStream(await req.send());
    if (res.statusCode < 200 || res.statusCode >= 300) {
      var detail = 'Gửi thất bại (${res.statusCode})';
      try {
        final body = jsonDecode(utf8.decode(res.bodyBytes));
        if (body is Map && body['detail'] is String) detail = body['detail'];
      } catch (_) {}
      throw ApiException(res.statusCode, detail);
    }
  }
}
