import '../data/models/driver_account.dart';
import 'api_client.dart';

class DriverApi {
  DriverApi({ApiClient? client}) : _c = client ?? ApiClient();
  final ApiClient _c;

  Future<DriverAccount> register({
    required String name,
    required String phone,
    required String licenseNumber,
  }) async {
    final j = await _c.post('/drivers/register', {
      'name': name,
      'phone': phone,
      'license_number': licenseNumber,
    });
    return DriverAccount.fromJson(j as Map<String, dynamic>);
  }

  /// Trả null nếu tài khoản chưa đăng ký hồ sơ (backend 404).
  Future<DriverAccount?> me({bool forceRefresh = false}) async {
    try {
      final j = await _c.get('/drivers/me', forceRefresh: forceRefresh);
      return DriverAccount.fromJson(j as Map<String, dynamic>);
    } on ApiException catch (e) {
      if (e.statusCode == 404) return null;
      rethrow;
    }
  }
}
