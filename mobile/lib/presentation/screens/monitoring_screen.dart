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
  // Chặn bấm chồng: nếu người dùng bấm nút lần 2 trong lúc request quyền /
  // start() còn đang chạy dở, permission_handler ném PlatformException
  // "A request for permissions is already running" (đã thấy khi chạy thật
  // trên emulator).
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
    final statuses = await [Permission.camera, Permission.notification].request();
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
          const SnackBar(content: Text('Cần quyền Camera & Thông báo để giám sát')),
        );
        return;
      }
      await vm.start();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Không thể bắt đầu giám sát: $e')),
      );
    } finally {
      if (mounted) setState(() => _isToggling = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final vm = context.watch<MonitoringViewModel>();

    return WithForegroundTask(
      child: Scaffold(
        appBar: AppBar(title: const Text('Giám sát an toàn lái xe')),
        body: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              AspectRatio(
                aspectRatio: 3 / 4,
                child: _CameraPreview(controller: vm.cameraFrameBuffer.controller),
              ),
              const SizedBox(height: 16),
              _StatusCard(vm: vm),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: _isToggling ? null : () => _toggleMonitoring(vm),
                icon: Icon(vm.isMonitoring ? Icons.stop : Icons.play_arrow),
                label: Text(vm.isMonitoring ? 'Dừng giám sát' : 'Bắt đầu giám sát'),
              ),
              const SizedBox(height: 16),
              Expanded(child: _RecentLogList(logs: vm.recentLogs)),
            ],
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
      return const ColoredBox(
        color: Colors.black12,
        child: Center(child: Text('Camera chưa bật')),
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
    final (icon, color, label) = switch (vm.phase) {
      MonitoringPhase.idle => (Icons.hourglass_empty, Colors.grey, 'Chưa giám sát'),
      MonitoringPhase.calibrating => (
          Icons.tune,
          Colors.blue,
          'Đang hiệu chỉnh... ${vm.calibrationProgress}/${vm.calibrationTarget}',
        ),
      MonitoringPhase.monitoring => _monitoringStatus(vm.lastDrowsyProbability, vm.drowsyThreshold),
    };

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(icon, color: color),
            const SizedBox(width: 8),
            Text(label, style: Theme.of(context).textTheme.titleMedium),
          ],
        ),
      ),
    );
  }

  (IconData, Color, String) _monitoringStatus(double? probability, double threshold) {
    if (probability == null) {
      return (Icons.search, Colors.grey, 'Đang phân tích...');
    }
    final percent = (probability * 100).toStringAsFixed(0);
    if (probability >= threshold) {
      return (Icons.warning_amber, Colors.red, 'Cảnh báo: buồn ngủ! ($percent%)');
    }
    return (Icons.check_circle, Colors.green, 'Bình thường ($percent%)');
  }
}

class _RecentLogList extends StatelessWidget {
  const _RecentLogList({required this.logs});

  final List<EventLog> logs;

  @override
  Widget build(BuildContext context) {
    if (logs.isEmpty) {
      return const Center(child: Text('Chưa có sự cố nào được ghi nhận'));
    }
    return ListView.builder(
      itemCount: logs.length,
      itemBuilder: (context, index) {
        final log = logs[index];
        return ListTile(
          leading: const Icon(Icons.warning_amber_outlined),
          title: Text(log.message),
          subtitle: Text(log.timestamp.toString()),
        );
      },
    );
  }
}
