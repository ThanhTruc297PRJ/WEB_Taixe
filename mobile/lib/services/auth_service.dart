import 'package:firebase_auth/firebase_auth.dart';

/// Bọc Firebase Auth (email + mật khẩu). ViewModel dùng lớp này, không gọi
/// FirebaseAuth trực tiếp.
class AuthService {
  final FirebaseAuth _auth = FirebaseAuth.instance;

  Stream<User?> authState() => _auth.authStateChanges();
  User? get currentUser => _auth.currentUser;

  Future<UserCredential> signIn(String email, String password) =>
      _auth.signInWithEmailAndPassword(email: email.trim(), password: password);

  Future<UserCredential> signUp(String email, String password) =>
      _auth.createUserWithEmailAndPassword(
        email: email.trim(),
        password: password,
      );

  Future<void> signOut() => _auth.signOut();

  /// [forceRefresh] = true để lấy claim mới ngay sau khi admin duyệt.
  Future<String?> idToken({bool forceRefresh = false}) async {
    final user = _auth.currentUser;
    if (user == null) return null;
    return user.getIdToken(forceRefresh);
  }
}
