import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../viewmodels/auth_view_model.dart';

/// Màn chặn khi tài khoản chưa dùng được: chờ duyệt / bị từ chối / bị khoá.
class StatusScreen extends StatelessWidget {
  const StatusScreen({super.key, required this.state});

  final GateState state;

  ({IconData icon, Color color, String title, String message}) get _content {
    switch (state) {
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
          message: 'Hồ sơ của bạn đã gửi. Vui lòng chờ quản trị viên duyệt.',
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    final vm = context.watch<AuthViewModel>();
    final c = _content;
    final reason = vm.account?.rejectReason;

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
