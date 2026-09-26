import 'package:flutter/material.dart';
import 'package:fluentui_system_icons/fluentui_system_icons.dart';
import 'package:provider/provider.dart';

import '../viewmodels/auth_view_model.dart';
import 'monitoring_screen.dart';
import 'report_screen.dart';
import 'maintenance_screen.dart';
import 'music_screen.dart';
import 'profile_screen.dart';
import 'map_screen.dart';

class AppScaffold extends StatefulWidget {
  const AppScaffold({super.key});

  @override
  State<AppScaffold> createState() => _AppScaffoldState();
}

class _AppScaffoldState extends State<AppScaffold> {
  int _currentIndex = 2; // Mặc định ở giữa là Giám sát AI

  final List<Widget> _screens = const [
    MapScreen(), // 0: Bản đồ
    ReportScreen(), // 1: Báo cáo
    MonitoringScreen(), // 2: Giám sát AI (Trọng tâm ở giữa)
    MaintenanceScreen(), // 3: Bảo trì
    MusicScreen(), // 4: Giải trí
    ProfileScreen(), // 5: Tài khoản cá nhân
  ];

  @override
  Widget build(BuildContext context) {
    final account = context.watch<AuthViewModel>().account;
    final activeIndex = _currentIndex == 5 ? 5 : _currentIndex;

    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.white.withValues(alpha: 0.85),
        elevation: 0,
        centerTitle: true,
        title: Text(
          _getScreenTitle(activeIndex),
          style: const TextStyle(
            color: Colors.black87,
            fontWeight: FontWeight.bold,
            fontSize: 18,
          ),
        ),
        actions: [
          // Nút Profile luôn xuất hiện ở góc trên bên phải mọi trang
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: GestureDetector(
              onTap: () => setState(() => _currentIndex = 5),
              child: Container(
                padding: const EdgeInsets.all(2),
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: _currentIndex == 5
                        ? const Color(0xFF2A8B88)
                        : Colors.grey.shade300,
                    width: 2,
                  ),
                ),
                child: CircleAvatar(
                  radius: 16,
                  backgroundColor: Colors.white,
                  backgroundImage: NetworkImage(
                    account?.photoUrl ??
                        'https://cdn-icons-png.flaticon.com/512/3135/3135715.png',
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFFE0F2F1), Color(0xFFF9FAFB)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 300),
          transitionBuilder: (Widget child, Animation<double> animation) {
            return FadeTransition(
              opacity: animation,
              child: SlideTransition(
                position:
                    Tween<Offset>(
                      begin: const Offset(0, 0.03),
                      end: Offset.zero,
                    ).animate(
                      CurvedAnimation(
                        parent: animation,
                        curve: Curves.easeOutCubic,
                      ),
                    ),
                child: child,
              ),
            );
          },
          child: KeyedSubtree(
            key: ValueKey<int>(activeIndex),
            child: _screens[activeIndex],
          ),
        ),
      ),
      bottomNavigationBar: Container(
        height: 75,
        margin: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(24),
          border: Border.all(
            color: Colors.white.withValues(alpha: 0.9),
            width: 1.5,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.08),
              blurRadius: 20,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _buildNavItem(
              0,
              FluentIcons.map_24_regular,
              FluentIcons.map_24_filled,
              'Bản đồ',
            ),
            _buildNavItem(
              1,
              FluentIcons.warning_24_regular,
              FluentIcons.warning_24_filled,
              'Báo cáo',
            ),

            // Nút Giám sát AI nổi bật chính giữa
            Transform.translate(
              offset: const Offset(0, -12),
              child: GestureDetector(
                onTap: () => setState(() => _currentIndex = 2),
                child: Container(
                  width: 60,
                  height: 60,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: const LinearGradient(
                      colors: [Color(0xFF2A8B88), Color(0xFF175452)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF2A8B88).withValues(alpha: 0.4),
                        blurRadius: 12,
                        offset: const Offset(0, 6),
                      ),
                    ],
                  ),
                  child: const Icon(
                    FluentIcons.camera_24_filled,
                    color: Colors.white,
                    size: 28,
                  ),
                ),
              ),
            ),

            _buildNavItem(
              3,
              FluentIcons.wrench_24_regular,
              FluentIcons.wrench_24_filled,
              'Bảo trì',
            ),
            _buildCustomNavItem(4, Icons.music_note_rounded, 'Giải trí'),
          ],
        ),
      ),
    );
  }

  Widget _buildNavItem(
    int index,
    IconData iconRegular,
    IconData iconFilled,
    String label,
  ) {
    final isSelected = _currentIndex == index;
    return InkWell(
      onTap: () => setState(() => _currentIndex = index),
      borderRadius: BorderRadius.circular(16),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              isSelected ? iconFilled : iconRegular,
              color: isSelected
                  ? const Color(0xFF2A8B88)
                  : Colors.grey.shade400,
              size: 22,
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: TextStyle(
                fontSize: 10,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                color: isSelected
                    ? const Color(0xFF2A8B88)
                    : Colors.grey.shade500,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCustomNavItem(int index, IconData iconData, String label) {
    final isSelected = _currentIndex == index;
    return InkWell(
      onTap: () => setState(() => _currentIndex = index),
      borderRadius: BorderRadius.circular(16),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              iconData,
              color: isSelected
                  ? const Color(0xFF2A8B88)
                  : Colors.grey.shade400,
              size: 22,
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: TextStyle(
                fontSize: 10,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                color: isSelected
                    ? const Color(0xFF2A8B88)
                    : Colors.grey.shade500,
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _getScreenTitle(int index) {
    switch (index) {
      case 0:
        return 'Bản Đồ & Hành Trình';
      case 1:
        return 'Báo Cáo Sự Cố';
      case 2:
        return 'Giám Sát AI';
      case 3:
        return 'Bảo Trì Phương Tiện';
      case 4:
        return 'Giải Trí & Âm Nhạc';
      case 5:
        return 'Tài Khoản Cá Nhân';
      default:
        return 'Hệ Thống';
    }
  }
}
