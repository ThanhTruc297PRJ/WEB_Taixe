import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:animate_do/animate_do.dart';
import 'package:fluentui_system_icons/fluentui_system_icons.dart';
import 'dart:ui';

import '../viewmodels/music_view_model.dart';
import 'radio_screen.dart';

class MusicScreen extends StatefulWidget {
  const MusicScreen({super.key});

  @override
  State<MusicScreen> createState() => _MusicScreenState();
}

class _MusicScreenState extends State<MusicScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final TextEditingController _searchController = TextEditingController();

  // Khởi tạo trực tiếp PageController để tránh lỗi LateInitializationError
  final PageController _pageController = PageController(viewportFraction: 0.75);

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _searchController.dispose();
    _pageController.dispose();
    super.dispose();
  }

  void _showNotice(MusicViewModel vm) {
    final text = vm.notice;
    if (text == null) return;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(
          SnackBar(
            content: Text(
              text,
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
            behavior: SnackBarBehavior.floating,
            backgroundColor: const Color(0xFF2A8B88),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
            ),
          ),
        );
      vm.clearNotice();
    });
  }

  Future<void> _confirmReport(MusicViewModel vm, SongModel song) async {
    final reasonCtrl = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Báo cáo bài hát'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '“${song.title}” — ${song.artist}',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: reasonCtrl,
              maxLines: 2,
              decoration: const InputDecoration(
                hintText: 'Lý do (không bắt buộc)',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Huỷ'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Gửi báo cáo'),
          ),
        ],
      ),
    );
    if (ok == true) {
      await vm.reportTrack(
        song,
        reason: reasonCtrl.text.trim().isEmpty ? null : reasonCtrl.text.trim(),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final musicVM = context.watch<MusicViewModel>();
    _showNotice(musicVM);

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 64, 16, 8),
              child: Row(
                children: [
                  Expanded(
                    child: Container(
                      height: 52,
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(26),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.05),
                            blurRadius: 16,
                            offset: const Offset(0, 4),
                          ),
                        ],
                      ),
                      child: TextField(
                        controller: _searchController,
                        style: const TextStyle(
                          color: Colors.black87,
                          fontSize: 15,
                          fontWeight: FontWeight.w500,
                        ),
                        decoration: InputDecoration(
                          hintText: 'Tìm bài hát...',
                          hintStyle: TextStyle(
                            color: Colors.grey.shade400,
                            fontWeight: FontWeight.normal,
                          ),
                          prefixIcon: const Icon(
                            FluentIcons.search_24_regular,
                            color: Color(0xFF2A8B88),
                            size: 22,
                          ),
                          suffixIcon: _searchController.text.isNotEmpty
                              ? IconButton(
                                  icon: const Icon(
                                    FluentIcons.dismiss_20_regular,
                                    color: Colors.grey,
                                    size: 20,
                                  ),
                                  onPressed: () {
                                    _searchController.clear();
                                    musicVM.clearSearch();
                                  },
                                )
                              : null,
                          border: InputBorder.none,
                          contentPadding: const EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 15,
                          ),
                        ),
                        onSubmitted: (val) {
                          FocusScope.of(context).unfocus();
                          _tabController.animateTo(0);
                          musicVM.searchMusic(val);
                        },
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Container(
                    height: 52,
                    width: 52,
                    decoration: BoxDecoration(
                      color: Colors.white,
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.05),
                          blurRadius: 16,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: IconButton(
                      tooltip: 'Radio FM',
                      icon: const Icon(
                        Icons.radio,
                        color: Color(0xFF2A8B88),
                        size: 24,
                      ),
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const RadioScreen(),
                          ),
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),

            Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: TabBar(
                controller: _tabController,
                indicatorColor: const Color(0xFF2A8B88),
                indicatorWeight: 3,
                indicatorSize: TabBarIndicatorSize.label,
                labelColor: const Color(0xFF2A8B88),
                unselectedLabelColor: Colors.grey.shade400,
                labelStyle: const TextStyle(
                  fontWeight: FontWeight.w800,
                  fontSize: 15,
                ),
                dividerColor: Colors.transparent,
                tabs: const [
                  Tab(text: 'Khám phá'),
                  Tab(text: 'Yêu thích'),
                  Tab(text: 'Đã nghe'),
                ],
              ),
            ),

            Expanded(
              child: TabBarView(
                controller: _tabController,
                physics: const NeverScrollableScrollPhysics(),
                children: [
                  _buildCoverFlowTab(musicVM),
                  _buildStandardList(
                    musicVM.favorites,
                    musicVM,
                    'Chưa có bài hát yêu thích nào.',
                  ),
                  _buildStandardList(
                    musicVM.history,
                    musicVM,
                    'Lịch sử phát trống.',
                  ),
                ],
              ),
            ),
          ],
        ),
      ),

      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
      floatingActionButton: musicVM.currentTrack != null
          ? FadeInUp(
              duration: const Duration(milliseconds: 400),
              child: Padding(
                padding: const EdgeInsets.only(bottom: 90, left: 16, right: 16),
                child: _buildSmartPillPlayer(musicVM),
              ),
            )
          : null,
    );
  }

  Widget _buildCoverFlowTab(MusicViewModel musicVM) {
    if (musicVM.isLoading)
      return const Center(
        child: CircularProgressIndicator(color: Color(0xFF2A8B88)),
      );

    if (musicVM.searchResults.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: const Color(0xFF2A8B88).withValues(alpha: 0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                FluentIcons.music_note_2_24_regular,
                size: 56,
                color: Color(0xFF2A8B88),
              ),
            ),
            const SizedBox(height: 24),
            Text(
              'Không gian giải trí',
              style: TextStyle(
                color: Colors.grey.shade800,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Nhập tên bài hát để bắt đầu hành trình',
              style: TextStyle(color: Colors.grey.shade500, fontSize: 14),
            ),
          ],
        ),
      );
    }

    return PageView.builder(
      controller: _pageController,
      itemCount: musicVM.searchResults.length,
      itemBuilder: (context, index) {
        final song = musicVM.searchResults[index];
        final isCurrent = musicVM.currentTrack?.id == song.id;

        return AnimatedBuilder(
          animation: _pageController,
          builder: (context, child) {
            double value = 1.0;
            if (_pageController.position.haveDimensions) {
              value = _pageController.page! - index;
              value = (1 - (value.abs() * 0.25)).clamp(0.0, 1.0);
            }

            return Center(
              child: SizedBox(
                height: Curves.easeOut.transform(value) * 400,
                width: Curves.easeOut.transform(value) * 300,
                child: child,
              ),
            );
          },
          child: GestureDetector(
            onTap: () => musicVM.playTrack(song),
            child: Container(
              margin: const EdgeInsets.symmetric(horizontal: 10, vertical: 20),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(32),
                boxShadow: [
                  BoxShadow(
                    color: (isCurrent ? const Color(0xFF2A8B88) : Colors.black)
                        .withValues(alpha: 0.15),
                    blurRadius: 24,
                    offset: const Offset(0, 12),
                  ),
                ],
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(32),
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    song.artworkUrl != null
                        ? Image.network(song.artworkUrl!, fit: BoxFit.cover)
                        : Container(
                            color: Colors.grey.shade200,
                            child: const Icon(
                              FluentIcons.music_note_1_24_filled,
                              size: 80,
                              color: Colors.grey,
                            ),
                          ),

                    Container(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                          colors: [
                            Colors.transparent,
                            Colors.black.withValues(alpha: 0.8),
                          ],
                          stops: const [0.5, 1.0],
                        ),
                      ),
                    ),

                    Positioned(
                      top: 12,
                      right: 12,
                      child: Material(
                        color: Colors.black.withValues(alpha: 0.35),
                        shape: const CircleBorder(),
                        child: IconButton(
                          tooltip: 'Báo cáo bài hát',
                          icon: const Icon(
                            FluentIcons.flag_24_regular,
                            color: Colors.white,
                            size: 20,
                          ),
                          onPressed: () => _confirmReport(musicVM, song),
                        ),
                      ),
                    ),

                    Padding(
                      padding: const EdgeInsets.all(24.0),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.end,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      song.title,
                                      style: const TextStyle(
                                        color: Colors.white,
                                        fontSize: 22,
                                        fontWeight: FontWeight.bold,
                                        height: 1.2,
                                      ),
                                      maxLines: 2,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                    const SizedBox(height: 6),
                                    Text(
                                      song.artist,
                                      style: TextStyle(
                                        color: Colors.white.withValues(
                                          alpha: 0.8,
                                        ),
                                        fontSize: 16,
                                      ),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ],
                                ),
                              ),
                              Container(
                                decoration: BoxDecoration(
                                  color: isCurrent
                                      ? const Color(0xFF2A8B88)
                                      : Colors.white.withValues(alpha: 0.2),
                                  shape: BoxShape.circle,
                                  border: Border.all(
                                    color: Colors.white.withValues(alpha: 0.5),
                                    width: 2,
                                  ),
                                ),
                                child: IconButton(
                                  iconSize: 36,
                                  icon: Icon(
                                    isCurrent && musicVM.isPlaying
                                        ? Icons.pause_rounded
                                        : Icons.play_arrow_rounded,
                                    color: Colors.white,
                                  ),
                                  onPressed: () => musicVM.playTrack(song),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildStandardList(
    List<SongModel> list,
    MusicViewModel musicVM,
    String emptyMessage,
  ) {
    if (list.isEmpty)
      return Center(
        child: Text(
          emptyMessage,
          style: TextStyle(color: Colors.grey.shade500),
        ),
      );

    return ListView.builder(
      padding: const EdgeInsets.only(left: 16, right: 16, top: 16, bottom: 180),
      itemCount: list.length,
      itemBuilder: (context, index) {
        final song = list[index];
        final isCurrent = musicVM.currentTrack?.id == song.id;

        return Container(
          margin: const EdgeInsets.only(bottom: 12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: isCurrent
                  ? const Color(0xFF2A8B88).withValues(alpha: 0.4)
                  : Colors.transparent,
            ),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.03),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: ListTile(
            contentPadding: const EdgeInsets.symmetric(
              horizontal: 12,
              vertical: 6,
            ),
            leading: ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: song.artworkUrl != null
                  ? Image.network(
                      song.artworkUrl!,
                      width: 56,
                      height: 56,
                      fit: BoxFit.cover,
                    )
                  : Container(
                      width: 56,
                      height: 56,
                      color: Colors.grey.shade200,
                      child: const Icon(Icons.music_note, color: Colors.grey),
                    ),
            ),
            title: Text(
              song.title,
              style: TextStyle(
                fontWeight: FontWeight.w700,
                color: isCurrent ? const Color(0xFF2A8B88) : Colors.black87,
              ),
            ),
            subtitle: Text(
              song.artist,
              style: TextStyle(color: Colors.grey.shade500, fontSize: 13),
            ),
            trailing: IconButton(
              icon: Icon(
                isCurrent && musicVM.isPlaying
                    ? Icons.pause_circle_filled
                    : Icons.play_circle_fill,
                size: 36,
                color: isCurrent
                    ? const Color(0xFF2A8B88)
                    : Colors.grey.shade300,
              ),
              onPressed: () => musicVM.playTrack(song),
            ),
            onTap: () => musicVM.playTrack(song),
            onLongPress: () => _confirmReport(musicVM, song),
          ),
        );
      },
    );
  }

  Widget _buildSmartPillPlayer(MusicViewModel musicVM) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(40),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
        child: Container(
          height: 72,
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.85),
            borderRadius: BorderRadius.circular(40),
            border: Border.all(
              color: Colors.white.withValues(alpha: 0.5),
              width: 1.5,
            ),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF2A8B88).withValues(alpha: 0.15),
                blurRadius: 24,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: Row(
            children: [
              RotationTransition(
                turns: AlwaysStoppedAnimation(
                  musicVM.isPlaying
                      ? (DateTime.now().millisecondsSinceEpoch % 3000) / 3000
                      : 0,
                ),
                child: CircleAvatar(
                  radius: 28,
                  backgroundImage: musicVM.currentTrack!.artworkUrl != null
                      ? NetworkImage(musicVM.currentTrack!.artworkUrl!)
                      : null,
                  backgroundColor: const Color(
                    0xFF2A8B88,
                  ).withValues(alpha: 0.2),
                  child: musicVM.currentTrack!.artworkUrl == null
                      ? const Icon(Icons.music_note, color: Color(0xFF2A8B88))
                      : null,
                ),
              ),
              const SizedBox(width: 16),

              Expanded(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      musicVM.currentTrack!.title,
                      style: const TextStyle(
                        fontWeight: FontWeight.w800,
                        fontSize: 15,
                        color: Colors.black87,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      musicVM.currentTrack!.artist,
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

              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    decoration: const BoxDecoration(
                      color: Color(0xFF2A8B88),
                      shape: BoxShape.circle,
                    ),
                    child: IconButton(
                      icon: Icon(
                        musicVM.isPlaying
                            ? Icons.pause_rounded
                            : Icons.play_arrow_rounded,
                        color: Colors.white,
                        size: 24,
                      ),
                      onPressed: () => musicVM.togglePlayPause(),
                    ),
                  ),
                  const SizedBox(width: 4),
                  IconButton(
                    icon: Icon(
                      Icons.close_rounded,
                      color: Colors.grey.shade400,
                      size: 24,
                    ),
                    onPressed: () => musicVM.closePlayer(),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
