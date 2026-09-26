import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter_foreground_task/flutter_foreground_task.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:provider/provider.dart';

import '../../data/models/event_log.dart';
import '../viewmodels/monitoring_view_model.dart';

class MonitoringScreen extends StatefulWidget {
  const MonitoringScreen({super.key});

  @override
  State<MonitoringScreen> createState() => _MonitoringScreenState();
}

class _MonitoringScreenState extends State<MonitoringScreen> {
  bool _isToggling = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<MonitoringViewModel>()
        ..initForegroundTask()
        ..loadRecentLogs();
    });
  }

  Future<bool> _ensurePermissions() async {
    final statuses = await [
      Permission.camera,
      Permission.notification,
    ].request();
    return statuses.values.every((s) => s.isGranted);
  }

  Future<void> _toggleMonitoring(MonitoringViewModel vm) async {
    if (_isToggling) return;
    setState(() => _isToggling = true);
    try {
      if (vm.isMonitoring) {
        await vm.stop();
        return;
      }
      if (!await _ensurePermissions()) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Cần quyền Camera & Thông báo để giám sát'),
          ),
        );
        return;
      }
      await vm.start();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Không thể bắt đầu giám sát: $e')));
    } finally {
      if (mounted) setState(() => _isToggling = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final vm = context.watch<MonitoringViewModel>();

    return WithForegroundTask(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(16, 90, 16, 120),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'Luồng Camera',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                    ),
                    IconButton(
                      icon: const Icon(
                        Icons.switch_camera,
                        color: Color(0xFF2A8B88),
                      ),
                      tooltip: 'Đổi nguồn Camera',
                      onPressed: vm.isMonitoring
                          ? () => vm.switchCamera()
                          : null,
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.9),
                      width: 1.5,
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.04),
                        blurRadius: 16,
                        offset: const Offset(0, 6),
                      ),
                      BoxShadow(
                        color: const Color(0xFF2A8B88).withValues(alpha: 0.08),
                        blurRadius: 24,
                        offset: const Offset(0, 10),
                      ),
                    ],
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(24),
                    child: AspectRatio(
                      aspectRatio: 16 / 11,
                      child: _CameraPreview(
                        controller: vm.cameraFrameBuffer.controller,
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                _StatusCard(vm: vm),
                const SizedBox(height: 16),
                Container(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: vm.isMonitoring
                          ? [Colors.redAccent, Colors.red.shade800]
                          : [const Color(0xFF2A8B88), const Color(0xFF175452)],
                    ),
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color:
                            (vm.isMonitoring
                                    ? Colors.redAccent
                                    : const Color(0xFF2A8B88))
                                .withValues(alpha: 0.3),
                        blurRadius: 12,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: SizedBox(
                    height: 52,
                    child: ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.transparent,
                        shadowColor: Colors.transparent,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                      ),
                      onPressed: _isToggling
                          ? null
                          : () => _toggleMonitoring(vm),
                      icon: Icon(
                        vm.isMonitoring
                            ? Icons.stop_circle_outlined
                            : Icons.play_circle_fill,
                      ),
                      label: Text(
                        vm.isMonitoring
                            ? 'Dừng giám sát AI'
                            : 'Bắt đầu giám sát',
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 0.5,
                        ),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                const Text(
                  'Nhật ký sự cố',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: Colors.black87,
                  ),
                ),
                const SizedBox(height: 8),
                _RecentLogList(logs: vm.recentLogs),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _CameraPreview extends StatelessWidget {
  const _CameraPreview({required this.controller});
  final CameraController? controller;

  @override
  Widget build(BuildContext context) {
    if (controller == null || !controller!.value.isInitialized) {
      return Container(
        color: Colors.grey.shade100,
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.videocam_off, size: 48, color: Colors.grey.shade400),
              const SizedBox(height: 8),
              Text(
                'Camera chưa bật',
                style: TextStyle(
                  color: Colors.grey.shade500,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      );
    }
    return CameraPreview(controller!);
  }
}

class _StatusCard extends StatelessWidget {
  const _StatusCard({required this.vm});
  final MonitoringViewModel vm;

  @override
  Widget build(BuildContext context) {
    if (vm.capturingIncident) {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.orange.shade50,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.orange.shade200),
        ),
        child: const Row(
          children: [
            SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(
                strokeWidth: 2.5,
                color: Colors.orange,
              ),
            ),
            SizedBox(width: 14),
            Expanded(
              child: Text(
                'Đang ghi lại video sự cố (10 giây)...',
                style: TextStyle(
                  color: Colors.deepOrange,
                  fontWeight: FontWeight.bold,
                  fontSize: 13,
                ),
              ),
            ),
          ],
        ),
      );
    }

    final (icon, color, bgColor, label) = switch (vm.phase) {
      MonitoringPhase.idle => (
        Icons.hourglass_empty,
        Colors.grey.shade600,
        Colors.grey.shade100,
        'Chưa giám sát',
      ),
      MonitoringPhase.monitoring => _monitoringStatus(
        vm.lastDrowsyProbability,
        vm.drowsyThreshold,
      ),
    };

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 28),
          const SizedBox(width: 14),
          Expanded(
            child: Text(
              label,
              style: TextStyle(
                color: color,
                fontSize: 14,
                fontWeight: FontWeight.w800,
              ),
            ),
          ),
        ],
      ),
    );
  }

  (IconData, Color, Color, String) _monitoringStatus(
    double? probability,
    double threshold,
  ) {
    if (probability == null)
      return (
        Icons.analytics,
        const Color(0xFF2A8B88),
        const Color(0xFF2A8B88).withValues(alpha: 0.1),
        'AI đang phân tích...',
      );
    final percent = (probability * 100).toStringAsFixed(0);
    if (probability >= threshold) {
      return (
        Icons.warning_amber_rounded,
        Colors.red,
        Colors.red.shade50,
        'Cảnh báo: BUỒN NGỦ! ($percent%)',
      );
    }
    return (
      Icons.check_circle_rounded,
      Colors.green,
      Colors.green.shade50,
      'Trạng thái tỉnh táo ($percent%)',
    );
  }
}

class _RecentLogList extends StatelessWidget {
  const _RecentLogList({required this.logs});
  final List<EventLog> logs;

  @override
  Widget build(BuildContext context) {
    if (logs.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: Colors.white.withValues(alpha: 0.8),
            width: 1.5,
          ),
        ),
        child: Center(
          child: Text(
            'Chưa có sự cố nào được ghi nhận',
            style: TextStyle(color: Colors.grey.shade500, fontSize: 13),
          ),
        ),
      );
    }
    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: logs.length,
      itemBuilder: (context, index) {
        final log = logs[index];
        return Container(
          margin: const EdgeInsets.only(bottom: 8),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
              color: Colors.white.withValues(alpha: 0.8),
              width: 1,
            ),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.02),
                blurRadius: 6,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: ListTile(
            dense: true,
            leading: CircleAvatar(
              radius: 16,
              backgroundColor: Colors.red.shade50,
              child: const Icon(
                Icons.warning_amber_rounded,
                color: Colors.redAccent,
                size: 18,
              ),
            ),
            title: Text(
              log.message,
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                color: Colors.black87,
                fontSize: 13,
              ),
            ),
            subtitle: Text(
              log.timestamp.toString(),
              style: TextStyle(color: Colors.grey.shade500, fontSize: 11),
            ),
          ),
        );
      },
    );
  }
}
