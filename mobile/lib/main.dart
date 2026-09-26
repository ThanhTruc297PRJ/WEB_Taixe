import 'dart:ui';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:fluentui_system_icons/fluentui_system_icons.dart';
import 'package:animate_do/animate_do.dart';

import 'firebase_options.dart';
import 'services/fcm_service.dart';
import 'presentation/viewmodels/auth_view_model.dart';
import 'presentation/viewmodels/monitoring_view_model.dart';
import 'presentation/viewmodels/music_view_model.dart';
import 'presentation/viewmodels/maintenance_view_model.dart';

import 'presentation/screens/auth/login_screen.dart';
import 'presentation/screens/auth/register_screen.dart';
import 'presentation/screens/gate/status_screen.dart';
import 'presentation/screens/monitoring_screen.dart';
import 'presentation/screens/map_screen.dart';
import 'presentation/screens/report_screen.dart';
import 'presentation/screens/maintenance_screen.dart';
import 'presentation/screens/music_screen.dart';
import 'presentation/screens/profile_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
  FirebaseMessaging.onBackgroundMessage(firebaseMessagingBackgroundHandler);
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthViewModel()),
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
        textTheme: GoogleFonts.montserratTextTheme(ThemeData.light().textTheme),
        scaffoldBackgroundColor: const Color(0xFFF9FAFB),
        colorScheme: const ColorScheme.light(
          primary: Color(0xFF2A8B88),
          surface: Colors.white,
        ),
      ),
      home: const _Gate(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class _Gate extends StatelessWidget {
  const _Gate();

  @override
  Widget build(BuildContext context) {
    final gate = context.watch<AuthViewModel>().gate;
    switch (gate) {
      case GateState.loading:
        return const Scaffold(
          body: Center(
            child: CircularProgressIndicator(color: Color(0xFF2A8B88)),
          ),
        );
      case GateState.login:
        return const LoginScreen();
      case GateState.register:
        return const RegisterScreen(profileOnly: true);
      case GateState.emailUnverified:
      case GateState.pending:
      case GateState.rejected:
      case GateState.locked:
        return StatusScreen(state: gate);
      case GateState.ready:
        return const MainScreen();
    }
  }
}

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _currentIndex = 2; // Mặc định mở tab 2 là GIÁM SÁT AI ở chính giữa

  // Sắp xếp đúng thứ tự các màn hình:
  // 0: Bản đồ, 1: Báo cáo, 2: Giám sát AI (TRỌNG TÂM Ở GIỮA), 3: Bảo trì, 4: Giải trí, 5: Tài khoản
  final List<Widget> _screens = [
    const MapScreen(), // Index 0
    const ReportScreen(), // Index 1
    const MonitoringScreen(), // Index 2 (Chính giữa)
    const MaintenanceScreen(), // Index 3
    const MusicScreen(), // Index 4
    const ProfileScreen(), // Index 5 (Tài khoản)
  ];

  final List<String> _titles = [
    'Bản Đồ Hành Trình',
    'Báo Cáo Sự Cố',
    'Giám Sát AI Trọng Tâm',
    'Bảo Trì Phương Tiện',
    'Giải Trí An Toàn',
    'Tài Khoản Cá Nhân',
  ];

  @override
  void initState() {
    super.initState();
    final driverId = context.read<AuthViewModel>().account?.id;
    if (driverId != null) {
      FcmService().init(driverId);
    }
  }

  @override
  Widget build(BuildContext context) {
    final musicVM = context.watch<MusicViewModel>();
    final account = context.watch<AuthViewModel>().account;
    final activeIndex = _currentIndex == 5 ? 5 : _currentIndex;

    return Scaffold(
      extendBody: true,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        flexibleSpace: ClipRect(
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 16, sigmaY: 16),
            child: Container(color: Colors.white.withValues(alpha: 0.85)),
          ),
        ),
        title: Text(
          _titles[activeIndex],
          style: const TextStyle(
            color: Colors.black87,
            fontWeight: FontWeight.w800,
            fontSize: 17,
            letterSpacing: 0.5,
          ),
        ),
        actions: [
          // Nút Profile luôn hiển thị ở góc trên bên phải mọi trang
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
      body: Stack(
        children: [
          IndexedStack(index: activeIndex, children: _screens),
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
          child: Container(
            height: 68,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(32),
              border: Border.all(color: Colors.grey.shade200),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF2A8B88).withValues(alpha: 0.1),
                  blurRadius: 24,
                  offset: const Offset(0, 8),
                ),
              ],
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                // 0: Bản đồ
                _buildNavItem(
                  0,
                  FluentIcons.map_24_regular,
                  FluentIcons.map_24_filled,
                ),
                // 1: Báo cáo
                _buildNavItem(
                  1,
                  FluentIcons.warning_24_regular,
                  FluentIcons.warning_24_filled,
                ),

                // 2: GIÁM SÁT AI (Nút tròn nổi bật chính giữa)
                Transform.translate(
                  offset: const Offset(0, -10),
                  child: GestureDetector(
                    onTap: () => setState(() => _currentIndex = 2),
                    child: Container(
                      width: 56,
                      height: 56,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: const LinearGradient(
                          colors: [Color(0xFF2A8B88), Color(0xFF175452)],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(
                              0xFF2A8B88,
                            ).withValues(alpha: 0.4),
                            blurRadius: 12,
                            offset: const Offset(0, 6),
                          ),
                        ],
                      ),
                      child: const Icon(
                        FluentIcons.video_person_24_filled,
                        color: Colors.white,
                        size: 26,
                      ),
                    ),
                  ),
                ),

                // 3: Bảo trì
                _buildNavItem(
                  3,
                  FluentIcons.wrench_24_regular,
                  FluentIcons.wrench_24_filled,
                ),
                // 4: Giải trí
                _buildNavItem(
                  4,
                  FluentIcons.music_note_1_24_regular,
                  FluentIcons.music_note_1_24_filled,
                ),
              ],
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
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: isSelected
              ? const Color(0xFF2A8B88).withValues(alpha: 0.1)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Icon(
          isSelected ? iconFilled : iconRegular,
          color: isSelected ? const Color(0xFF2A8B88) : Colors.grey.shade400,
          size: 24,
        ),
      ),
    );
  }

  Widget _buildGlassMiniPlayer(MusicViewModel musicVM) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.95),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.grey.shade200),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 16,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(16),
            child: musicVM.currentTrack!.artworkUrl != null
                ? Image.network(
                    musicVM.currentTrack!.artworkUrl!,
                    width: 48,
                    height: 48,
                    fit: BoxFit.cover,
                  )
                : Container(
                    width: 48,
                    height: 48,
                    color: const Color(0xFF2A8B88).withValues(alpha: 0.1),
                    child: const Icon(
                      FluentIcons.music_note_1_24_filled,
                      color: Color(0xFF2A8B88),
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
                    color: Colors.black87,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 2),
                Text(
                  musicVM.currentTrack!.artist,
                  style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          Container(
            decoration: const BoxDecoration(
              color: Color(0xFF2A8B88),
              shape: BoxShape.circle,
            ),
            child: IconButton(
              icon: Icon(
                musicVM.isPlaying
                    ? FluentIcons.pause_24_filled
                    : FluentIcons.play_24_filled,
                color: Colors.white,
                size: 20,
              ),
              onPressed: () => musicVM.togglePlayPause(),
            ),
          ),
          const SizedBox(width: 4),
          IconButton(
            icon: Icon(
              FluentIcons.dismiss_24_regular,
              color: Colors.grey.shade400,
              size: 24,
            ),
            onPressed: () => musicVM.closePlayer(),
          ),
        ],
      ),
    );
  }
}
