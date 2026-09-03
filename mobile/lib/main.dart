import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_zoom_drawer/flutter_zoom_drawer.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:fluentui_system_icons/fluentui_system_icons.dart';
import 'package:animate_do/animate_do.dart';

import 'presentation/viewmodels/monitoring_view_model.dart';
import 'presentation/viewmodels/music_view_model.dart';
import 'presentation/viewmodels/maintenance_view_model.dart';

import 'presentation/screens/monitoring_screen.dart';
import 'presentation/screens/map_screen.dart';
import 'presentation/screens/report_screen.dart';
import 'presentation/screens/music_screen.dart';
import 'presentation/screens/maintenance_screen.dart';
import 'presentation/screens/profile_screen.dart'; // Import màn hình profile

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => MonitoringViewModel()),
        ChangeNotifierProvider(create: (_) => MusicViewModel()),
        ChangeNotifierProvider(create: (_) => MaintenanceViewModel()),
      ],
      child: const MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Hệ Thống Giám Sát Tài Xế',
      theme: ThemeData(
        useMaterial3: true,
        textTheme: GoogleFonts.montserratTextTheme(),
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFD32F2F),
          primary: const Color(0xFFD32F2F),
          surface: Colors.white,
        ),
        scaffoldBackgroundColor: const Color(0xFFF8F9FA),
      ),
      home: const MainLayout(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class MainLayout extends StatefulWidget {
  const MainLayout({super.key});

  @override
  State<MainLayout> createState() => _MainLayoutState();
}

class _MainLayoutState extends State<MainLayout> {
  final ZoomDrawerController _drawerController = ZoomDrawerController();
  int _currentIndex = 0;

  @override
  Widget build(BuildContext context) {
    return ZoomDrawer(
      controller: _drawerController,
      menuScreen: MenuScreen(
        currentIndex: _currentIndex,
        onItemSelected: (index) {
          setState(() => _currentIndex = index);
          _drawerController.close?.call();
        },
      ),
      mainScreen: MainContentScreen(
        currentIndex: _currentIndex,
        drawerController: _drawerController,
      ),
      borderRadius: 30.0,
      showShadow: true,
      angle: -8.0,
      drawerShadowsBackgroundColor: Colors.grey.shade300,
      slideWidth: MediaQuery.of(context).size.width * 0.75,
      menuBackgroundColor: const Color(0xFFD32F2F),
    );
  }
}

class MenuScreen extends StatelessWidget {
  final int currentIndex;
  final Function(int) onItemSelected;

  const MenuScreen({
    super.key,
    required this.currentIndex,
    required this.onItemSelected,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFD32F2F),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 40),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              FadeInDown(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Header Menu cá nhân hóa
                    const CircleAvatar(
                      radius: 30,
                      backgroundColor: Colors.white,
                      backgroundImage: NetworkImage(
                        'https://cdn-icons-png.flaticon.com/512/3135/3135715.png',
                      ),
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      'Võ Quyền Anh',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Tài xế nội bộ',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.7),
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 40),

              _buildMenuItem(
                0,
                'Giám Sát Camera',
                FluentIcons.video_person_24_regular,
                FluentIcons.video_person_24_filled,
              ),
              _buildMenuItem(
                1,
                'Bản Đồ Hành Trình',
                FluentIcons.map_24_regular,
                FluentIcons.map_24_filled,
              ),
              _buildMenuItem(
                2,
                'Báo Cáo Sự Cố',
                FluentIcons.warning_24_regular,
                FluentIcons.warning_24_filled,
              ),
              _buildMenuItem(
                3,
                'Bảo Trì & Kiểm Định',
                FluentIcons.wrench_24_regular,
                FluentIcons.wrench_24_filled,
              ),
              _buildMenuItem(
                4,
                'Giải Trí & Radio',
                FluentIcons.music_note_1_24_regular,
                FluentIcons.music_note_1_24_filled,
              ),

              const Padding(
                padding: EdgeInsets.symmetric(vertical: 8),
                child: Divider(color: Colors.white24, thickness: 1),
              ),

              // Mục tài khoản được tách riêng xuống dưới cùng
              _buildMenuItem(
                5,
                'Tài Khoản',
                FluentIcons.person_24_regular,
                FluentIcons.person_24_filled,
              ),

              const Spacer(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMenuItem(
    int index,
    String title,
    IconData iconRegular,
    IconData iconFilled,
  ) {
    final isSelected = currentIndex == index;
    return FadeInLeft(
      delay: Duration(milliseconds: 50 * index),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: isSelected
              ? Colors.white.withOpacity(0.15)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(16),
        ),
        child: ListTile(
          onTap: () => onItemSelected(index),
          leading: Icon(
            isSelected ? iconFilled : iconRegular,
            color: Colors.white,
            size: 24,
          ),
          title: Text(
            title,
            style: TextStyle(
              color: Colors.white,
              fontSize: 15,
              fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
            ),
          ),
        ),
      ),
    );
  }
}

class MainContentScreen extends StatelessWidget {
  final int currentIndex;
  final ZoomDrawerController drawerController;

  MainContentScreen({
    super.key,
    required this.currentIndex,
    required this.drawerController,
  });

  final List<Widget> _screens = [
    const MonitoringScreen(),
    const MapScreen(),
    const ReportScreen(),
    const MaintenanceScreen(),
    const MusicScreen(),
    const ProfileScreen(), // Thêm màn hình Profile vào index 5
  ];

  final List<String> _titles = [
    'Giám Sát AI',
    'Bản Đồ',
    'Báo Cáo',
    'Bảo Trì Xe',
    'Giải Trí',
    'Tài Khoản',
  ];

  @override
  Widget build(BuildContext context) {
    final musicVM = context.watch<MusicViewModel>();

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: const Color(0xFFF8F9FA),
        elevation: 0,
        centerTitle: true,
        leading: IconButton(
          icon: const Icon(
            FluentIcons.line_horizontal_3_20_regular,
            color: Colors.black87,
            size: 28,
          ),
          onPressed: () => drawerController.toggle?.call(),
        ),
        title: Text(
          _titles[currentIndex],
          style: const TextStyle(
            color: Colors.black87,
            fontWeight: FontWeight.bold,
            fontSize: 18,
          ),
        ),
      ),
      body: Stack(
        children: [
          IndexedStack(index: currentIndex, children: _screens),

          if (musicVM.currentTrack != null)
            Positioned(
              bottom: 24,
              left: 20,
              right: 20,
              child: FadeInUp(
                duration: const Duration(milliseconds: 600),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(24),
                  child: BackdropFilter(
                    filter: ImageFilter.blur(sigmaX: 15, sigmaY: 15),
                    child: Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.8),
                        borderRadius: BorderRadius.circular(24),
                        border: Border.all(
                          color: Colors.white.withOpacity(0.5),
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFFD32F2F).withOpacity(0.15),
                            offset: const Offset(0, 8),
                            blurRadius: 20,
                          ),
                        ],
                      ),
                      child: Row(
                        children: [
                          ClipOval(
                            child: Image.network(
                              musicVM.currentTrack!['artworkUrl100'] ?? '',
                              width: 50,
                              height: 50,
                              fit: BoxFit.cover,
                              errorBuilder: (_, __, ___) => const CircleAvatar(
                                backgroundColor: Color(0xFFD32F2F),
                                child: Icon(
                                  FluentIcons.music_note_1_24_filled,
                                  color: Colors.white,
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text(
                                  musicVM.currentTrack!['trackName'] ?? '',
                                  style: const TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 15,
                                    color: Colors.black87,
                                  ),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  musicVM.currentTrack!['artistName'] ?? '',
                                  style: TextStyle(
                                    color: Colors.grey.shade600,
                                    fontSize: 13,
                                    fontWeight: FontWeight.w500,
                                  ),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ],
                            ),
                          ),
                          Container(
                            decoration: BoxDecoration(
                              color: const Color(0xFFD32F2F),
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: IconButton(
                              icon: Icon(
                                musicVM.isPlaying
                                    ? FluentIcons.pause_24_filled
                                    : FluentIcons.play_24_filled,
                                color: Colors.white,
                              ),
                              onPressed: () => musicVM.togglePlayPause(),
                            ),
                          ),
                          const SizedBox(width: 4),
                          IconButton(
                            icon: const Icon(
                              FluentIcons.dismiss_24_regular,
                              color: Colors.grey,
                            ),
                            onPressed: () => musicVM.closePlayer(),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
