import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../viewmodels/auth_view_model.dart';

/// Màn chặn khi tài khoản chưa dùng được: chưa xác thực email / chờ duyệt /
/// bị từ chối / bị khoá.
class StatusScreen extends StatelessWidget {
  const StatusScreen({super.key, required this.state});

  final GateState state;

  ({IconData icon, Color color, String title, String message}) get _content {
    switch (state) {
      case GateState.emailUnverified:
        return (
          icon: Icons.mark_email_unread_outlined,
          color: Colors.amberAccent,
          title: 'Chưa xác thực email',
          message:
              'Kiểm tra hộp thư (kể cả mục Spam) và bấm vào link xác thực '
              'trước khi tiếp tục. Quản trị viên chỉ duyệt được sau khi bạn '
              'xác thực email.',
        );
      case GateState.rejected:
        return (
          icon: Icons.cancel_outlined,
          color: Colors.redAccent,
          title: 'Đăng ký bị từ chối',
          message: 'Quản trị viên đã từ chối hồ sơ của bạn.',
        );
      case GateState.locked:
        return (
          icon: Icons.lock_outline,
          color: Colors.orangeAccent,
          title: 'Tài khoản đã bị khoá',
          message: 'Liên hệ quản trị viên để được mở khoá.',
        );
      case GateState.pending:
      default:
        return (
          icon: Icons.hourglass_top,
          color: Colors.cyanAccent,
          title: 'Đang chờ duyệt',
          message:
              'Email đã xác thực. Hồ sơ của bạn đã gửi — vui lòng chờ quản '
              'trị viên duyệt.',
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    final vm = context.watch<AuthViewModel>();
    final c = _content;
    final reason = vm.account?.rejectReason;
    final isEmailUnverified = state == GateState.emailUnverified;

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(c.icon, size: 72, color: c.color),
                const SizedBox(height: 16),
                Text(
                  c.title,
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  c.message,
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.white70),
                ),
                if (isEmailUnverified && vm.account?.id != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    vm.account!.name,
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Colors.white38, fontSize: 12),
                  ),
                ],
                if (state == GateState.rejected &&
                    reason != null &&
                    reason.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.redAccent.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      'Lý do: $reason',
                      style: const TextStyle(color: Colors.redAccent),
                    ),
                  ),
                ],
                const SizedBox(height: 32),
                FilledButton.icon(
                  onPressed:
                      vm.busy ? null : () => vm.refreshAccount(force: true),
                  icon: const Icon(Icons.refresh),
                  label: const Text('Kiểm tra lại'),
                ),
                if (isEmailUnverified) ...[
                  const SizedBox(height: 8),
                  OutlinedButton.icon(
                    onPressed: vm.busy
                        ? null
                        : () async {
                            final ok = await vm.resendVerificationEmail();
                            if (ok && context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text('Đã gửi lại email xác thực'),
                                ),
                              );
                            }
                          },
                    icon: const Icon(Icons.mail_outline),
                    label: const Text('Gửi lại email xác thực'),
                  ),
                ],
                if (vm.actionError != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    vm.actionError!,
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Colors.redAccent, fontSize: 12),
                  ),
                ],
                const SizedBox(height: 8),
                TextButton(
                  onPressed: vm.busy ? null : () => vm.signOut(),
                  child: const Text('Đăng xuất'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
