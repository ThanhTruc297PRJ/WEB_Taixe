import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import 'package:animate_do/animate_do.dart';
import 'package:fluentui_system_icons/fluentui_system_icons.dart';

import '../viewmodels/maintenance_view_model.dart';

class MaintenanceScreen extends StatelessWidget {
  const MaintenanceScreen({super.key});

  Future<void> _selectDate(BuildContext context, bool isInspection) async {
    final vm = context.read<MaintenanceViewModel>();
    final initialDate = isInspection
        ? (vm.inspectionDate ?? DateTime.now())
        : (vm.oilChangeDate ?? DateTime.now());

    final picked = await showDatePicker(
      context: context,
      initialDate: initialDate,
      firstDate: DateTime.now(),
      lastDate: DateTime(2030),
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: const ColorScheme.light(
              primary: Color(0xFF2A8B88),
              onPrimary: Colors.white,
              onSurface: Colors.black,
            ),
          ),
          child: child!,
        );
      },
    );

    if (picked != null) {
      if (isInspection) {
        vm.saveInspectionDate(picked);
      } else {
        vm.saveOilChangeDate(picked);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final vm = context.watch<MaintenanceViewModel>();
    final dateFormat = DateFormat('dd/MM/yyyy');

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 105, 16, 120),
        children: [
          FadeInDown(
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF2A8B88).withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: const Color(0xFF2A8B88).withValues(alpha: 0.2),
                ),
              ),
              child: const Text(
                'Theo dõi tình trạng phương tiện để đảm bảo an toàn tuyệt đối trên mọi hành trình.',
                style: TextStyle(
                  color: Color(0xFF2A8B88),
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
          const SizedBox(height: 20),

          FadeInLeft(
            delay: const Duration(milliseconds: 100),
            child: _buildMaintenanceCard(
              context: context,
              title: 'Hạn Đăng Kiểm',
              icon: FluentIcons.document_text_24_filled,
              date: vm.inspectionDate,
              daysLeft: vm.daysUntilInspection,
              dateFormat: dateFormat,
              onTap: () => _selectDate(context, true),
            ),
          ),
          const SizedBox(height: 16),

          FadeInRight(
            delay: const Duration(milliseconds: 200),
            child: _buildMaintenanceCard(
              context: context,
              title: 'Lịch Thay Nhớt Máy',
              icon: FluentIcons.drop_24_filled,
              date: vm.oilChangeDate,
              daysLeft: vm.daysUntilOilChange,
              dateFormat: dateFormat,
              onTap: () => _selectDate(context, false),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMaintenanceCard({
    required BuildContext context,
    required String title,
    required IconData icon,
    required DateTime? date,
    required int daysLeft,
    required DateFormat dateFormat,
    required VoidCallback onTap,
  }) {
    final isWarning = date != null && daysLeft <= 15;

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(
          color: isWarning
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
          BoxShadow(
            color: const Color(0xFF2A8B88).withValues(alpha: 0.06),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(24),
        child: InkWell(
          borderRadius: BorderRadius.circular(24),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: isWarning
                        ? Colors.red.shade50
                        : const Color(0xFF2A8B88).withValues(alpha: 0.1),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    icon,
                    color: isWarning
                        ? Colors.redAccent
                        : const Color(0xFF2A8B88),
                    size: 28,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Colors.black87,
                        ),
                      ),
                      const SizedBox(height: 6),
                      if (date == null)
                        Text(
                          'Chưa thiết lập',
                          style: TextStyle(color: Colors.grey.shade400),
                        )
                      else ...[
                        Text(
                          'Đến hạn: ${dateFormat.format(date)}',
                          style: TextStyle(
                            fontSize: 13,
                            color: Colors.grey.shade600,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          daysLeft < 0
                              ? 'Đã quá hạn ${daysLeft.abs()} ngày!'
                              : 'Còn lại $daysLeft ngày',
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                            color: isWarning
                                ? Colors.redAccent
                                : const Color(0xFF2A8B88),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                Icon(
                  FluentIcons.chevron_right_24_regular,
                  color: Colors.grey.shade400,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
