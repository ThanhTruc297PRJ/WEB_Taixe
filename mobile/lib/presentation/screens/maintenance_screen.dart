import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:animate_do/animate_do.dart';
import 'package:fluentui_system_icons/fluentui_system_icons.dart';

import '../../services/vehicle_job_api.dart';
import 'job_complete_screen.dart';

const _teal = Color(0xFF2A8B88);

/// Lịch bảo trì + đăng kiểm do quản lý tạo trên web cho xe tài xế đang lái.
/// Làm xong thì tài xế bấm "Báo đã xong" (ảnh hoá đơn/tem, số km, chi phí);
/// quản lý xác nhận trên web thì lịch mới tính là hoàn tất.
class MaintenanceScreen extends StatefulWidget {
  const MaintenanceScreen({super.key});

  @override
  State<MaintenanceScreen> createState() => _MaintenanceScreenState();
}

class _MaintenanceScreenState extends State<MaintenanceScreen> {
  final _api = VehicleJobApi();
  final _dateFormat = DateFormat('dd/MM/yyyy');
  List<VehicleJob> _jobs = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load({bool showSpinner = true}) async {
    setState(() {
      _loading = showSpinner;
      _error = null;
    });
    try {
      final jobs = await _api.mine();
      if (!mounted) return;
      setState(() {
        _jobs = jobs;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = 'Không tải được lịch bảo trì';
      });
    }
  }

  Future<void> _openComplete(VehicleJob job) async {
    final sent = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => JobCompleteScreen(job: job)),
    );
    if (sent == true) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Đã gửi — chờ quản lý xác nhận')),
      );
      _load(showSpinner: false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: RefreshIndicator(
        color: _teal,
        edgeOffset: 100,
        onRefresh: () => _load(showSpinner: false),
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(16, 105, 16, 120),
          children: [
            FadeInDown(
              child: Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: _teal.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: _teal.withValues(alpha: 0.2)),
                ),
                child: const Text(
                  'Lịch bảo trì và đăng kiểm của xe bạn phụ trách. Làm xong, '
                  'bấm "Báo đã xong" và chụp ảnh hoá đơn hoặc tem để quản lý xác nhận.',
                  style: TextStyle(
                    color: _teal,
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 20),
            ..._buildBody(),
          ],
        ),
      ),
    );
  }

  List<Widget> _buildBody() {
    if (_loading) {
      return const [
        Padding(
          padding: EdgeInsets.only(top: 60),
          child: Center(child: CircularProgressIndicator(color: _teal)),
        ),
      ];
    }
    if (_error != null || _jobs.isEmpty) {
      return [
        Padding(
          padding: const EdgeInsets.only(top: 40),
          child: Column(
            children: [
              Icon(
                _error != null
                    ? FluentIcons.cloud_off_24_regular
                    : FluentIcons.checkmark_circle_24_regular,
                size: 48,
                color: Colors.grey.shade400,
              ),
              const SizedBox(height: 12),
              Text(
                _error ?? 'Không có lịch bảo trì hay đăng kiểm nào cần làm',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.grey.shade600),
              ),
              if (_error != null)
                TextButton.icon(
                  onPressed: _load,
                  icon: const Icon(Icons.refresh),
                  label: const Text('Thử lại'),
                ),
            ],
          ),
        ),
      ];
    }
    return [
      for (var i = 0; i < _jobs.length; i++)
        FadeInUp(
          delay: Duration(milliseconds: 60 * i),
          child: Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: _JobCard(
              job: _jobs[i],
              dateFormat: _dateFormat,
              onComplete: () => _openComplete(_jobs[i]),
            ),
          ),
        ),
    ];
  }
}

class _JobCard extends StatelessWidget {
  const _JobCard({
    required this.job,
    required this.dateFormat,
    required this.onComplete,
  });

  final VehicleJob job;
  final DateFormat dateFormat;
  final VoidCallback onComplete;

  @override
  Widget build(BuildContext context) {
    final today = DateUtils.dateOnly(DateTime.now());
    final daysLeft = job.dueDate == null
        ? null
        : DateUtils.dateOnly(job.dueDate!).difference(today).inDays;
    final overdue = !job.isAwaiting && daysLeft != null && daysLeft < 0;
    final warn = !job.isAwaiting && daysLeft != null && daysLeft <= 7;
    final accent = job.isAwaiting
        ? const Color(0xFF7C3AED)
        : (warn ? Colors.redAccent : _teal);

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(
          color: warn
              ? Colors.redAccent.withValues(alpha: 0.4)
              : Colors.white.withValues(alpha: 0.9),
          width: 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: accent.withValues(alpha: 0.1),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  job.isInspection
                      ? FluentIcons.document_text_24_filled
                      : FluentIcons.wrench_24_filled,
                  color: accent,
                  size: 24,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      job.title,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      [
                        if (job.plateNumber != null) 'Xe ${job.plateNumber}',
                        if (job.place != null && job.place!.isNotEmpty)
                          job.place!,
                      ].join(' · '),
                      style: TextStyle(
                        fontSize: 13,
                        color: Colors.grey.shade600,
                      ),
                    ),
                  ],
                ),
              ),
              _StatusChip(job: job, overdue: overdue),
            ],
          ),
          const SizedBox(height: 14),
          if (job.dueDate != null)
            Text(
              '${job.isInspection ? 'Tem hết hạn' : 'Hẹn'}: '
              '${dateFormat.format(job.dueDate!)}'
              '${job.isAwaiting ? '' : (overdue ? ' — quá hạn ${daysLeft.abs()} ngày' : ' — còn $daysLeft ngày')}',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: job.isAwaiting ? Colors.grey.shade700 : accent,
              ),
            ),
          if (job.dueOdometerKm != null) ...[
            const SizedBox(height: 4),
            Text(
              'Hoặc khi xe chạy tới ${NumberFormat.decimalPattern('vi').format(job.dueOdometerKm)} km',
              style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
            ),
          ],
          if (job.appointmentAt != null) ...[
            const SizedBox(height: 4),
            Text(
              'Giờ hẹn: ${DateFormat('HH:mm dd/MM/yyyy').format(job.appointmentAt!)}',
              style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
            ),
          ],
          if (!job.isAwaiting && job.rejectionReason != null) ...[
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.orange.shade50,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                'Quản lý trả lại: ${job.rejectionReason}',
                style: TextStyle(fontSize: 13, color: Colors.orange.shade900),
              ),
            ),
          ],
          const SizedBox(height: 14),
          SizedBox(
            width: double.infinity,
            child: job.isAwaiting
                ? OutlinedButton.icon(
                    onPressed: null,
                    icon: const Icon(FluentIcons.clock_24_regular),
                    label: const Text('Đã gửi — chờ quản lý xác nhận'),
                  )
                : FilledButton.icon(
                    style: FilledButton.styleFrom(
                      backgroundColor: _teal,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                    ),
                    onPressed: onComplete,
                    icon: const Icon(FluentIcons.checkmark_circle_24_regular),
                    label: Text(
                      job.rejectionReason != null
                          ? 'Gửi lại báo cáo'
                          : 'Báo đã xong',
                    ),
                  ),
          ),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.job, required this.overdue});

  final VehicleJob job;
  final bool overdue;

  @override
  Widget build(BuildContext context) {
    final (label, color) = job.isAwaiting
        ? ('Chờ xác nhận', const Color(0xFF7C3AED))
        : job.rejectionReason != null
        ? ('Bị trả lại', Colors.orange.shade800)
        : overdue
        ? ('Quá hạn', Colors.redAccent)
        : ('Chưa làm', _teal);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w600,
          color: color,
        ),
      ),
    );
  }
}
