import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:animate_do/animate_do.dart';

import '../../viewmodels/auth_view_model.dart';

/// Đăng ký tài xế. Có 2 chế độ:
///  - [profileOnly] = false (mặc định): tạo tài khoản Firebase + gửi hồ sơ.
///    Dùng từ màn đăng nhập.
///  - [profileOnly] = true: đã đăng nhập nhưng thiếu hồ sơ, chỉ gửi hồ sơ.
///    Dùng khi cổng vào ở trạng thái GateState.register.
class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key, this.profileOnly = false});

  final bool profileOnly;

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _form = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _name = TextEditingController();
  final _phone = TextEditingController();
  final _license = TextEditingController();

  @override
  void dispose() {
    for (final c in [_email, _password, _name, _phone, _license]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_form.currentState!.validate()) return;
    final vm = context.read<AuthViewModel>();

    final ok = widget.profileOnly
        ? await vm.registerProfile(
            name: _name.text.trim(),
            phone: _phone.text.trim(),
            licenseNumber: _license.text.trim(),
          )
        : await vm.signUpAndRegister(
            email: _email.text,
            password: _password.text,
            name: _name.text.trim(),
            phone: _phone.text.trim(),
            licenseNumber: _license.text.trim(),
          );

    if (ok && mounted && !widget.profileOnly) {
      // Cổng vào (AppGate) sẽ tự chuyển sang màn "chờ duyệt".
      Navigator.of(context).maybePop();
    }
  }

  InputDecoration _fieldDecoration({
    required String label,
    required IconData icon,
  }) {
    OutlineInputBorder border(Color color, double width) =>
        OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: color, width: width),
        );
    return InputDecoration(
      labelText: label,
      labelStyle: const TextStyle(color: Colors.white54),
      prefixIcon: Icon(icon, color: Colors.cyanAccent.withValues(alpha: 0.85)),
      filled: true,
      fillColor: Colors.white.withValues(alpha: 0.05),
      contentPadding:
          const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      border: border(Colors.white.withValues(alpha: 0.08), 1),
      enabledBorder: border(Colors.white.withValues(alpha: 0.08), 1),
      focusedBorder: border(Colors.cyanAccent, 1.4),
      errorBorder: border(Colors.redAccent.withValues(alpha: 0.6), 1),
      focusedErrorBorder: border(Colors.redAccent, 1.4),
    );
  }

  Widget _sectionLabel(String text) => Padding(
        padding: const EdgeInsets.only(left: 4, bottom: 10),
        child: Text(
          text.toUpperCase(),
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w700,
            letterSpacing: 0.8,
            color: Colors.cyanAccent.withValues(alpha: 0.7),
          ),
        ),
      );

  Widget _sectionCard({required List<Widget> fields}) => Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFF151D30).withValues(alpha: 0.6),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: Colors.white.withValues(alpha: 0.06)),
        ),
        child: Column(children: fields),
      );

  @override
  Widget build(BuildContext context) {
    final vm = context.watch<AuthViewModel>();

    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: const Text('Đăng ký tài xế'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        // Màn này khi profileOnly=true là màn GỐC (GateState.register, đã
        // đăng nhập nhưng chưa có hồ sơ) -> không có back tự động. Cần nút
        // đăng xuất để thoát được nếu lỡ đăng nhập nhầm tài khoản (VD tài
        // khoản admin không có hồ sơ tài xế), không thì bị kẹt luôn ở đây.
        actions: widget.profileOnly
            ? [
                IconButton(
                  tooltip: 'Đăng xuất',
                  icon: const Icon(Icons.logout),
                  onPressed: vm.busy
                      ? null
                      : () => context.read<AuthViewModel>().signOut(),
                ),
              ]
            : null,
      ),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFF10182E), Color(0xFF0B101E)],
          ),
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(24, 12, 24, 32),
            child: Form(
              key: _form,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  FadeInDown(
                    duration: const Duration(milliseconds: 450),
                    child: Center(
                      child: Column(
                        children: [
                          Container(
                            width: 76,
                            height: 76,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              gradient: LinearGradient(
                                colors: [
                                  Colors.cyanAccent.withValues(alpha: 0.25),
                                  Colors.cyanAccent.withValues(alpha: 0.05),
                                ],
                              ),
                              border: Border.all(
                                color: Colors.cyanAccent.withValues(alpha: 0.4),
                                width: 1.5,
                              ),
                            ),
                            child: const Icon(
                              Icons.person_add_alt_1_rounded,
                              size: 34,
                              color: Colors.cyanAccent,
                            ),
                          ),
                          const SizedBox(height: 16),
                          const Text(
                            'Tạo hồ sơ tài xế',
                            style: TextStyle(
                              fontSize: 21,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            widget.profileOnly
                                ? 'Hoàn tất hồ sơ để bắt đầu sử dụng'
                                : 'Vài bước nhanh để bắt đầu sử dụng',
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                              color: Colors.white54,
                              fontSize: 13,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 28),
                  if (!widget.profileOnly) ...[
                    FadeInUp(
                      duration: const Duration(milliseconds: 450),
                      delay: const Duration(milliseconds: 80),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _sectionLabel('Tài khoản đăng nhập'),
                          _sectionCard(
                            fields: [
                              TextFormField(
                                controller: _email,
                                style: const TextStyle(color: Colors.white),
                                keyboardType: TextInputType.emailAddress,
                                autocorrect: false,
                                decoration: _fieldDecoration(
                                  label: 'Email',
                                  icon: Icons.email_outlined,
                                ),
                                validator: (v) => (v == null || !v.contains('@'))
                                    ? 'Email không hợp lệ'
                                    : null,
                              ),
                              const SizedBox(height: 14),
                              TextFormField(
                                controller: _password,
                                obscureText: true,
                                style: const TextStyle(color: Colors.white),
                                decoration: _fieldDecoration(
                                  label: 'Mật khẩu',
                                  icon: Icons.lock_outline,
                                ),
                                validator: (v) => (v == null || v.length < 6)
                                    ? 'Tối thiểu 6 ký tự'
                                    : null,
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),
                  ],
                  FadeInUp(
                    duration: const Duration(milliseconds: 450),
                    delay: const Duration(milliseconds: 140),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _sectionLabel('Hồ sơ tài xế'),
                        _sectionCard(
                          fields: [
                            TextFormField(
                              controller: _name,
                              style: const TextStyle(color: Colors.white),
                              textCapitalization: TextCapitalization.words,
                              decoration: _fieldDecoration(
                                label: 'Họ tên',
                                icon: Icons.badge_outlined,
                              ),
                              validator: (v) => (v == null || v.trim().isEmpty)
                                  ? 'Nhập họ tên'
                                  : null,
                            ),
                            const SizedBox(height: 14),
                            TextFormField(
                              controller: _phone,
                              style: const TextStyle(color: Colors.white),
                              keyboardType: TextInputType.phone,
                              decoration: _fieldDecoration(
                                label: 'Số điện thoại',
                                icon: Icons.phone_outlined,
                              ),
                              validator: (v) =>
                                  (v == null || v.trim().length < 8)
                                      ? 'SĐT không hợp lệ'
                                      : null,
                            ),
                            const SizedBox(height: 14),
                            TextFormField(
                              controller: _license,
                              style: const TextStyle(color: Colors.white),
                              decoration: _fieldDecoration(
                                label: 'Số bằng lái',
                                icon: Icons.drive_eta_outlined,
                              ),
                              validator: (v) => (v == null || v.trim().isEmpty)
                                  ? 'Nhập số bằng lái'
                                  : null,
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  if (vm.actionError != null) ...[
                    const SizedBox(height: 16),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 12,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.redAccent.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(
                          color: Colors.redAccent.withValues(alpha: 0.3),
                        ),
                      ),
                      child: Row(
                        children: [
                          const Icon(
                            Icons.error_outline,
                            color: Colors.redAccent,
                            size: 18,
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              vm.actionError!,
                              style: const TextStyle(
                                color: Colors.redAccent,
                                fontSize: 13,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                  const SizedBox(height: 28),
                  FadeInUp(
                    duration: const Duration(milliseconds: 450),
                    delay: const Duration(milliseconds: 200),
                    child: SizedBox(
                      height: 54,
                      child: DecoratedBox(
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(16),
                          gradient: const LinearGradient(
                            colors: [Colors.cyanAccent, Color(0xFF00B8D4)],
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.cyanAccent.withValues(alpha: 0.25),
                              blurRadius: 16,
                              offset: const Offset(0, 6),
                            ),
                          ],
                        ),
                        child: Material(
                          color: Colors.transparent,
                          child: InkWell(
                            borderRadius: BorderRadius.circular(16),
                            onTap: vm.busy ? null : _submit,
                            child: Center(
                              child: vm.busy
                                  ? const SizedBox(
                                      height: 22,
                                      width: 22,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2.4,
                                        color: Colors.black87,
                                      ),
                                    )
                                  : const Text(
                                      'Gửi đăng ký',
                                      style: TextStyle(
                                        color: Colors.black87,
                                        fontWeight: FontWeight.bold,
                                        fontSize: 16,
                                      ),
                                    ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),
                  Text(
                    widget.profileOnly
                        ? 'Hồ sơ sẽ được quản trị viên duyệt trước khi dùng.'
                        : 'Sau khi gửi, kiểm tra email để xác thực, rồi chờ '
                            'quản trị viên duyệt trước khi dùng.',
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Colors.white38, fontSize: 12),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
