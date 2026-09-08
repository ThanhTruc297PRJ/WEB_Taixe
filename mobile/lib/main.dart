import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:fluentui_system_icons/fluentui_system_icons.dart';
import 'package:animate_do/animate_do.dart';

import 'presentation/viewmodels/monitoring_view_model.dart';
import 'presentation/viewmodels/music_view_model.dart';
import 'presentation/viewmodels/maintenance_view_model.dart';

import 'presentation/screens/monitoring_screen.dart';
import 'presentation/screens/map_screen.dart';
import 'presentation/screens/report_screen.dart';
import 'presentation/screens/maintenance_screen.dart';
import 'presentation/screens/music_screen.dart';
import 'presentation/screens/profile_screen.dart';

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
        textTheme: GoogleFonts.montserratTextTheme(ThemeData.dark().textTheme),
        scaffoldBackgroundColor: const Color(0xFF0B101E),
        colorScheme: const ColorScheme.dark(
          primary: Colors.cyanAccent,
          surface: Color(0xFF151D30),
        ),
      ),
      home: const MainScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _currentIndex = 0;

  final List<Widget> _screens = [
    const MonitoringScreen(),
    const MapScreen(),
    const ReportScreen(),
    const MaintenanceScreen(),
    const MusicScreen(),
    const ProfileScreen(),
  ];

  final List<String> _titles = [
    'Giám Sát AI',
    'Bản Đồ Hành Trình',
    'Báo Cáo Sự Cố',
    'Bảo Trì Phương Tiện',
    'Giải Trí An Toàn',
    'Tài Khoản Cá Nhân',
  ];

  @override
  Widget build(BuildContext context) {
    final musicVM = context.watch<MusicViewModel>();

    return Scaffold(
      extendBody: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        flexibleSpace: ClipRect(
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 12, sigmaY: 12),
            child: Container(
              color: const Color(0xFF0B101E).withValues(alpha: 0.75),
            ),
          ),
        ),
        title: Text(
          _titles[_currentIndex],
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
            fontSize: 17,
            letterSpacing: 1.1,
          ),
        ),
      ),
      body: Stack(
        children: [
          IndexedStack(index: _currentIndex, children: _screens),
          if (musicVM.currentTrack != null)
            Positioned(
              bottom: 95,
              left: 16,
              right: 16,
              child: FadeInUp(
                duration: const Duration(milliseconds: 500),
                child: _buildGlassMiniPlayer(musicVM),
              ),
            ),
        ],
      ),
      bottomNavigationBar: FadeInUp(
        duration: const Duration(milliseconds: 700),
        child: Padding(
          padding: const EdgeInsets.only(left: 16, right: 16, bottom: 18),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(28),
            child: BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 16, sigmaY: 16),
              child: Container(
                height: 68,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.06),
                  borderRadius: BorderRadius.circular(28),
                  border: Border.all(
                    color: Colors.white.withValues(alpha: 0.12),
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.4),
                      blurRadius: 20,
                      offset: const Offset(0, 10),
                    ),
                  ],
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    _buildNavItem(
                      0,
                      FluentIcons.video_person_24_regular,
                      FluentIcons.video_person_24_filled,
                    ),
                    _buildNavItem(
                      1,
                      FluentIcons.map_24_regular,
                      FluentIcons.map_24_filled,
                    ),
                    _buildNavItem(
                      2,
                      FluentIcons.warning_24_regular,
                      FluentIcons.warning_24_filled,
                    ),
                    _buildNavItem(
                      3,
                      FluentIcons.wrench_24_regular,
                      FluentIcons.wrench_24_filled,
                    ),
                    _buildNavItem(
                      4,
                      FluentIcons.music_note_1_24_regular,
                      FluentIcons.music_note_1_24_filled,
                    ),
                    _buildNavItem(
                      5,
                      FluentIcons.person_24_regular,
                      FluentIcons.person_24_filled,
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem(int index, IconData iconRegular, IconData iconFilled) {
    final isSelected = _currentIndex == index;
    return GestureDetector(
      onTap: () => setState(() => _currentIndex = index),
      behavior: HitTestBehavior.opaque,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 250),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected
              ? Colors.cyanAccent.withValues(alpha: 0.15)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(18),
        ),
        child: Icon(
          isSelected ? iconFilled : iconRegular,
          color: isSelected ? Colors.cyanAccent : Colors.grey.shade400,
          size: 24,
        ),
      ),
    );
  }

  Widget _buildGlassMiniPlayer(MusicViewModel musicVM) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(20),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 16, sigmaY: 16),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: const Color(0xFF151D30).withValues(alpha: 0.85),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: Colors.cyanAccent.withValues(alpha: 0.35),
            ),
            boxShadow: [
              BoxShadow(
                color: Colors.cyanAccent.withValues(alpha: 0.1),
                blurRadius: 16,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Row(
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: musicVM.currentTrack!.artworkUrl != null
                    ? Image.network(
                        musicVM.currentTrack!.artworkUrl!,
                        width: 44,
                        height: 44,
                        fit: BoxFit.cover,
                        errorBuilder: (_, _, _) => Container(
                          width: 44,
                          height: 44,
                          color: Colors.white10,
                          child: const Icon(
                            FluentIcons.music_note_1_24_filled,
                            color: Colors.cyanAccent,
                          ),
                        ),
                      )
                    : Container(
                        width: 44,
                        height: 44,
                        color: Colors.cyanAccent.withValues(alpha: 0.15),
                        child: const Icon(
                          FluentIcons.folder_open_24_filled,
                          color: Colors.cyanAccent,
                          size: 20,
                        ),
                      ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      musicVM.currentTrack!.title,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                        color: Colors.white,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      musicVM.currentTrack!.artist,
                      style: TextStyle(
                        color: Colors.cyanAccent.withValues(alpha: 0.8),
                        fontSize: 12,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              Container(
                decoration: BoxDecoration(
                  color: Colors.cyanAccent,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: IconButton(
                  icon: Icon(
                    musicVM.isPlaying
                        ? FluentIcons.pause_24_filled
                        : FluentIcons.play_24_filled,
                    color: Colors.black,
                    size: 20,
                  ),
                  onPressed: () => musicVM.togglePlayPause(),
                ),
              ),
              const SizedBox(width: 4),
              IconButton(
                icon: const Icon(
                  FluentIcons.dismiss_24_regular,
                  color: Colors.grey,
                  size: 20,
                ),
                onPressed: () => musicVM.closePlayer(),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
