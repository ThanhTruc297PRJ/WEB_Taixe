import 'dart:async';

import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';

import '../../data/models/driver_account.dart';
import '../../services/api_client.dart';
import '../../services/auth_service.dart';
import '../../services/driver_api.dart';

enum GateState {
  loading, // đang kiểm tra
  login, // chưa đăng nhập
  register, // đã đăng nhập nhưng chưa có hồ sơ tài xế
  emailUnverified, // đã gửi hồ sơ nhưng chưa bấm link xác thực email
  pending, // đã xác thực email, chờ admin duyệt
  rejected, // hồ sơ bị từ chối
  locked, // tài khoản bị khoá
  ready, // đã duyệt -> vào app
}

/// Điều phối đăng nhập + trạng thái duyệt tài khoản. Cổng vào app xem
/// [gate] để quyết định hiện màn nào.
class AuthViewModel extends ChangeNotifier {
  AuthViewModel({AuthService? auth, DriverApi? driverApi})
      : _auth = auth ?? AuthService(),
        _driverApi = driverApi ?? DriverApi() {
    _sub = _auth.authState().listen(_onAuthChanged);
  }

  final AuthService _auth;
  final DriverApi _driverApi;
  StreamSubscription<User?>? _sub;

  GateState gate = GateState.loading;
  DriverAccount? account;

  /// Lỗi thao tác gần nhất (sai mật khẩu, email đã dùng...) — cho form hiển thị.
  String? actionError;
  bool busy = false;

  Future<void> _onAuthChanged(User? user) async {
    if (user == null) {
      account = null;
      _set(GateState.login);
      return;
    }
    await refreshAccount();
  }

  Future<void> refreshAccount({bool force = false}) async {
    _set(GateState.loading);
    try {
      if (force) {
        // Cập nhật cờ emailVerified cục bộ ngay nếu tài xế vừa bấm link xác
        // thực rồi quay lại app — nguồn sự thật vẫn là backend bên dưới.
        try {
          await _auth.reloadCurrentUser();
        } catch (_) {}
      }
      account = await _driverApi.me(forceRefresh: force);
      _set(_gateFor(account));
    } on ApiException catch (e) {
      if (e.statusCode == 401) {
        // Token hỏng / tài khoản đã xoá -> đăng nhập lại.
        await _auth.signOut();
      } else {
        actionError = e.message;
        _set(GateState.login);
      }
    } catch (e) {
      actionError = e.toString();
      _set(GateState.login);
    }
  }

  GateState _gateFor(DriverAccount? acc) {
    if (acc == null) return GateState.register;
    // Xác thực email trước, bất kể trạng thái hồ sơ — đúng thứ tự đăng ký ->
    // xác thực -> (mới) admin duyệt.
    if (!acc.emailVerified) return GateState.emailUnverified;
    switch (acc.status) {
      case DriverAccountStatus.active:
        return GateState.ready;
      case DriverAccountStatus.pending:
        return GateState.pending;
      case DriverAccountStatus.rejected:
        return GateState.rejected;
      case DriverAccountStatus.inactive:
        return GateState.locked;
      case DriverAccountStatus.unknown:
        return GateState.register;
    }
  }

  // ── Thao tác ──────────────────────────────────────────────────────────
  Future<bool> signIn(String email, String password) => _run(() async {
        await _auth.signIn(email, password);
      });

  /// Đăng ký mới: tạo tài khoản Firebase + gửi email xác thực + gửi hồ sơ.
  Future<bool> signUpAndRegister({
    required String email,
    required String password,
    required String name,
    required String phone,
    required String licenseNumber,
  }) =>
      _run(() async {
        await _auth.signUp(email, password);
        // Firebase tự gửi email kèm link xác thực — miễn phí, không cần
        // backend. Tài xế phải bấm link này trước khi admin duyệt được.
        await _auth.sendEmailVerification();
        await _driverApi.register(
          name: name,
          phone: phone,
          licenseNumber: licenseNumber,
        );
        await refreshAccount();
      });

  /// Gửi lại email xác thực (màn "Chưa xác thực email" gọi khi tài xế bấm
  /// "Gửi lại"). Firebase tự giới hạn tần suất gọi liên tục.
  Future<bool> resendVerificationEmail() =>
      _run(() => _auth.sendEmailVerification());

  /// Đã đăng nhập nhưng thiếu hồ sơ -> chỉ gửi hồ sơ.
  Future<bool> registerProfile({
    required String name,
    required String phone,
    required String licenseNumber,
  }) =>
      _run(() async {
        await _driverApi.register(
          name: name,
          phone: phone,
          licenseNumber: licenseNumber,
        );
        await refreshAccount();
      });

  Future<void> signOut() => _auth.signOut();

  Future<bool> _run(Future<void> Function() action) async {
    busy = true;
    actionError = null;
    notifyListeners();
    try {
      await action();
      return true;
    } on FirebaseAuthException catch (e) {
      actionError = _authErrorText(e.code);
      return false;
    } on ApiException catch (e) {
      actionError = e.message;
      return false;
    } catch (e) {
      actionError = e.toString();
      return false;
    } finally {
      busy = false;
      notifyListeners();
    }
  }

  String _authErrorText(String code) {
    switch (code) {
      case 'invalid-email':
        return 'Email không hợp lệ';
      case 'user-not-found':
      case 'wrong-password':
      case 'invalid-credential':
        return 'Email hoặc mật khẩu không đúng';
      case 'email-already-in-use':
        return 'Email này đã được đăng ký';
      case 'weak-password':
        return 'Mật khẩu quá yếu (tối thiểu 6 ký tự)';
      case 'too-many-requests':
        return 'Thử lại quá nhiều lần, vui lòng đợi';
      case 'network-request-failed':
        return 'Không có kết nối mạng';
      default:
        return 'Lỗi đăng nhập ($code)';
    }
  }

  void _set(GateState g) {
    gate = g;
    notifyListeners();
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }
}
