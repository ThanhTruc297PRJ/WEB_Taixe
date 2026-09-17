import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:animate_do/animate_do.dart';

import '../../viewmodels/auth_view_model.dart';

/// Quên mật khẩu: tài xế nhập email -> Firebase gửi link đặt lại mật khẩu
/// (miễn phí, tự xử lý phía Firebase, không cần backend riêng).
class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _form = GlobalKey<FormState>();
  final _email = TextEditingController();
  bool _sent = false;

  @override
  void dispose() {
    _email.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_form.currentState!.validate()) return;
    final vm = context.read<AuthViewModel>();
    final ok = await vm.sendPasswordResetEmail(_email.text);
    if (ok && mounted) setState(() => _sent = true);
  }

  InputDecoration _fieldDecoration() {
    OutlineInputBorder border(Color color, double width) =>
        OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: color, width: width),
        );
    return InputDecoration(
      labelText: 'Email',
      labelStyle: const TextStyle(color: Colors.white54),
      prefixIcon: Icon(
        Icons.email_outlined,
        color: Colors.cyanAccent.withValues(alpha: 0.85),
      ),
      filled: true,
      fillColor: Colors.white.withValues(alpha: 0.05),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      border: border(Colors.white.withValues(alpha: 0.08), 1),
      enabledBorder: border(Colors.white.withValues(alpha: 0.08), 1),
      focusedBorder: border(Colors.cyanAccent, 1.4),
      errorBorder: border(Colors.redAccent.withValues(alpha: 0.6), 1),
      focusedErrorBorder: border(Colors.redAccent, 1.4),
    );
  }

  @override
  Widget build(BuildContext context) {
    final vm = context.watch<AuthViewModel>();

    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: const Text('Quên mật khẩu'),
        backgroundColor: Colors.transparent,
        elevation: 0,
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
                            child: Icon(
                              _sent
                                  ? Icons.mark_email_read_outlined
                                  : Icons.lock_reset_rounded,
                              size: 34,
                              color: Colors.cyanAccent,
                            ),
                          ),
                          const SizedBox(height: 16),
                          Text(
                            _sent ? 'Kiểm tra email của bạn' : 'Quên mật khẩu?',
                            style: const TextStyle(
                              fontSize: 21,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            _sent
                                ? 'Đã gửi link đặt lại mật khẩu tới ${_email.text.trim()} — '
                                    'bấm vào link trong email (kể cả mục Spam) để đặt mật khẩu mới.'
                                : 'Nhập email đã đăng ký, chúng tôi sẽ gửi link để bạn đặt '
                                    'lại mật khẩu.',
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
                  if (!_sent) ...[
                    FadeInUp(
                      duration: const Duration(milliseconds: 450),
                      delay: const Duration(milliseconds: 80),
                      child: TextFormField(
                        controller: _email,
                        style: const TextStyle(color: Colors.white),
                        keyboardType: TextInputType.emailAddress,
                        autocorrect: false,
                        decoration: _fieldDecoration(),
                        validator: (v) => (v == null || !v.contains('@'))
                            ? 'Email không hợp lệ'
                            : null,
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
                      delay: const Duration(milliseconds: 140),
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
                                        'Gửi link đặt lại mật khẩu',
                                        style: TextStyle(
                                          color: Colors.black87,
                                          fontWeight: FontWeight.bold,
                                          fontSize: 15,
                                        ),
                                      ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ] else ...[
                    FadeInUp(
                      duration: const Duration(milliseconds: 450),
                      delay: const Duration(milliseconds: 80),
                      child: OutlinedButton(
                        onPressed: () => Navigator.of(context).maybePop(),
                        style: OutlinedButton.styleFrom(
                          minimumSize: const Size.fromHeight(54),
                          side: BorderSide(
                            color: Colors.cyanAccent.withValues(alpha: 0.4),
                          ),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                          ),
                        ),
                        child: const Text(
                          'Quay lại đăng nhập',
                          style: TextStyle(color: Colors.cyanAccent),
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
