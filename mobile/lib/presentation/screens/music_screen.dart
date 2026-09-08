import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:animate_do/animate_do.dart';
import 'package:fluentui_system_icons/fluentui_system_icons.dart';

import '../viewmodels/music_view_model.dart';

class MusicScreen extends StatefulWidget {
  const MusicScreen({super.key});

  @override
  State<MusicScreen> createState() => _MusicScreenState();
}

class _MusicScreenState extends State<MusicScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final musicVM = context.watch<MusicViewModel>();

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF0B101E), Color(0xFF151D30)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 8,
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.06),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(
                            color: Colors.white.withValues(alpha: 0.1),
                          ),
                        ),
                        child: TextField(
                          controller: _searchController,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 14,
                          ),
                          decoration: InputDecoration(
                            hintText: 'Tìm bài hát online...',
                            hintStyle: TextStyle(
                              color: Colors.white.withValues(alpha: 0.4),
                            ),
                            prefixIcon: const Icon(
                              FluentIcons.search_24_regular,
                              color: Colors.cyanAccent,
                              size: 20,
                            ),
                            suffixIcon: _searchController.text.isNotEmpty
                                ? IconButton(
                                    icon: const Icon(
                                      FluentIcons.dismiss_20_regular,
                                      color: Colors.grey,
                                      size: 18,
                                    ),
                                    onPressed: () {
                                      _searchController.clear();
                                      musicVM.clearSearch();
                                    },
                                  )
                                : null,
                            border: InputBorder.none,
                          ),
                          onSubmitted: (val) {
                            FocusScope.of(context).unfocus();
                            _tabController.animateTo(0);
                            musicVM.searchMusic(val);
                          },
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Container(
                      decoration: BoxDecoration(
                        color: Colors.cyanAccent.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: IconButton(
                        icon: const Icon(
                          FluentIcons.folder_open_24_filled,
                          color: Colors.cyanAccent,
                        ),
                        tooltip: 'Mở bài hát trong máy',
                        onPressed: () => musicVM.pickLocalAudioFile(),
                      ),
                    ),
                  ],
                ),
              ),
              TabBar(
                controller: _tabController,
                indicatorColor: Colors.cyanAccent,
                labelColor: Colors.cyanAccent,
                unselectedLabelColor: Colors.white54,
                tabs: const [
                  Tab(text: 'Khám phá'),
                  Tab(text: 'Yêu thích'),
                  Tab(text: 'Đã nghe'),
                ],
              ),
              Expanded(
                child: TabBarView(
                  controller: _tabController,
                  children: [
                    _buildOnlineTab(musicVM),
                    _buildSongList(
                      musicVM.favorites,
                      musicVM,
                      'Chưa có bài hát yêu thích nào.',
                    ),
                    _buildSongList(
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
      ),
    );
  }

  Widget _buildOnlineTab(MusicViewModel musicVM) {
    if (musicVM.isLoading) {
      return const Center(
        child: CircularProgressIndicator(color: Colors.cyanAccent),
      );
    }
    if (musicVM.searchResults.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              FluentIcons.music_note_2_24_regular,
              size: 56,
              color: Colors.white.withValues(alpha: 0.2),
            ),
            const SizedBox(height: 12),
            const Text(
              'Nhập từ khóa tìm kiếm hoặc chọn mở bài hát trong máy',
              style: TextStyle(color: Colors.white54, fontSize: 13),
            ),
          ],
        ),
      );
    }
    return _buildSongList(
      musicVM.searchResults,
      musicVM,
      'Không tìm thấy bài hát.',
    );
  }

  Widget _buildSongList(
    List<SongModel> list,
    MusicViewModel musicVM,
    String emptyMessage,
  ) {
    if (list.isEmpty) {
      return Center(
        child: Text(
          emptyMessage,
          style: const TextStyle(color: Colors.white54),
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.only(left: 16, right: 16, top: 12, bottom: 120),
      itemCount: list.length,
      itemBuilder: (context, index) {
        final song = list[index];
        final isCurrent = musicVM.currentTrack?.id == song.id;
        final isFav = musicVM.isFavorite(song.id);

        return FadeInUp(
          delay: Duration(milliseconds: 30 * (index % 10)),
          child: Container(
            margin: const EdgeInsets.only(bottom: 10),
            decoration: BoxDecoration(
              color: isCurrent
                  ? Colors.cyanAccent.withValues(alpha: 0.08)
                  : Colors.white.withValues(alpha: 0.04),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: isCurrent
                    ? Colors.cyanAccent.withValues(alpha: 0.3)
                    : Colors.white.withValues(alpha: 0.08),
              ),
            ),
            child: ListTile(
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 12,
                vertical: 2,
              ),
              leading: ClipRRect(
                borderRadius: BorderRadius.circular(10),
                child: song.isLocal || song.artworkUrl == null
                    ? Container(
                        width: 44,
                        height: 44,
                        color: Colors.cyanAccent.withValues(alpha: 0.15),
                        child: const Icon(
                          FluentIcons.music_note_1_24_filled,
                          color: Colors.cyanAccent,
                          size: 20,
                        ),
                      )
                    : Image.network(
                        song.artworkUrl!,
                        width: 44,
                        height: 44,
                        fit: BoxFit.cover,
                        errorBuilder: (_, _, _) => Container(
                          width: 44,
                          height: 44,
                          color: Colors.white10,
                          child: const Icon(
                            FluentIcons.music_note_1_24_regular,
                            color: Colors.white54,
                          ),
                        ),
                      ),
              ),
              title: Text(
                song.title,
                style: TextStyle(
                  color: isCurrent ? Colors.cyanAccent : Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              subtitle: Text(
                song.artist,
                style: const TextStyle(color: Colors.white60, fontSize: 12),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              trailing: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  IconButton(
                    icon: Icon(
                      isFav
                          ? FluentIcons.heart_24_filled
                          : FluentIcons.heart_24_regular,
                      color: isFav ? Colors.redAccent : Colors.white38,
                      size: 20,
                    ),
                    onPressed: () => musicVM.toggleFavorite(song),
                  ),
                  IconButton(
                    icon: Icon(
                      isCurrent && musicVM.isPlaying
                          ? FluentIcons.pause_circle_24_filled
                          : FluentIcons.play_circle_24_regular,
                      color: isCurrent ? Colors.cyanAccent : Colors.white70,
                      size: 28,
                    ),
                    onPressed: () => musicVM.playTrack(song),
                  ),
                ],
              ),
              onTap: () => musicVM.playTrack(song),
            ),
          ),
        );
      },
    );
  }
}
