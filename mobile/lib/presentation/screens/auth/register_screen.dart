import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

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

  @override
  Widget build(BuildContext context) {
    final vm = context.watch<AuthViewModel>();

    return Scaffold(
      appBar: AppBar(title: const Text('Đăng ký tài xế')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _form,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                if (!widget.profileOnly) ...[
                  TextFormField(
                    controller: _email,
                    keyboardType: TextInputType.emailAddress,
                    autocorrect: false,
                    decoration: const InputDecoration(
                      labelText: 'Email',
                      prefixIcon: Icon(Icons.email_outlined),
                    ),
                    validator: (v) => (v == null || !v.contains('@'))
                        ? 'Email không hợp lệ'
                        : null,
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _password,
                    obscureText: true,
                    decoration: const InputDecoration(
                      labelText: 'Mật khẩu',
                      prefixIcon: Icon(Icons.lock_outline),
                    ),
                    validator: (v) => (v == null || v.length < 6)
                        ? 'Tối thiểu 6 ký tự'
                        : null,
                  ),
                  const SizedBox(height: 16),
                ],
                TextFormField(
                  controller: _name,
                  textCapitalization: TextCapitalization.words,
                  decoration: const InputDecoration(
                    labelText: 'Họ tên',
                    prefixIcon: Icon(Icons.badge_outlined),
                  ),
                  validator: (v) =>
                      (v == null || v.trim().isEmpty) ? 'Nhập họ tên' : null,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _phone,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                    labelText: 'Số điện thoại',
                    prefixIcon: Icon(Icons.phone_outlined),
                  ),
                  validator: (v) =>
                      (v == null || v.trim().length < 8) ? 'SĐT không hợp lệ' : null,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _license,
                  decoration: const InputDecoration(
                    labelText: 'Số bằng lái',
                    prefixIcon: Icon(Icons.drive_eta_outlined),
                  ),
                  validator: (v) => (v == null || v.trim().isEmpty)
                      ? 'Nhập số bằng lái'
                      : null,
                ),
                if (vm.actionError != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    vm.actionError!,
                    style: const TextStyle(color: Colors.redAccent),
                  ),
                ],
                const SizedBox(height: 24),
                FilledButton(
                  onPressed: vm.busy ? null : _submit,
                  child: vm.busy
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Gửi đăng ký'),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Hồ sơ sẽ được quản trị viên duyệt trước khi dùng.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.white54, fontSize: 12),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
