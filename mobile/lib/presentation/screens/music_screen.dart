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

class _MusicScreenState extends State<MusicScreen> {
  final TextEditingController _searchController = TextEditingController();

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final musicVM = context.watch<MusicViewModel>();

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFFFFF0F0), Colors.white],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: Column(
          children: [
            // Thanh tìm kiếm thiết kế nổi (Floating Search Bar)
            FadeInDown(
              duration: const Duration(milliseconds: 500),
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 10),
                child: Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(20),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFFD32F2F).withOpacity(0.08),
                        blurRadius: 20,
                        offset: const Offset(0, 10),
                      ),
                    ],
                  ),
                  child: TextField(
                    controller: _searchController,
                    decoration: InputDecoration(
                      hintText: 'Tìm bài hát, ca sĩ...',
                      hintStyle: TextStyle(color: Colors.grey.shade400),
                      prefixIcon: const Icon(
                        FluentIcons.search_24_regular,
                        color: Color(0xFFD32F2F),
                      ),
                      suffixIcon: IconButton(
                        icon: const Icon(
                          FluentIcons.dismiss_24_regular,
                          color: Colors.grey,
                        ),
                        onPressed: () {
                          _searchController.clear();
                          musicVM.searchResults.clear();
                          musicVM.notifyListeners();
                        },
                      ),
                      border: InputBorder.none,
                      contentPadding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                    onSubmitted: (query) {
                      FocusScope.of(context).unfocus();
                      musicVM.searchMusic(query);
                    },
                  ),
                ),
              ),
            ),

            Expanded(
              child: musicVM.isLoading
                  ? const Center(
                      child: CircularProgressIndicator(
                        color: Color(0xFFD32F2F),
                      ),
                    )
                  : musicVM.searchResults.isEmpty
                  ? FadeInUp(
                      child: Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              FluentIcons.music_note_1_24_regular,
                              size: 64,
                              color: Colors.grey.shade300,
                            ),
                            const SizedBox(height: 16),
                            Text(
                              'Kho nhạc trực tuyến',
                              style: TextStyle(
                                color: Colors.grey.shade500,
                                fontSize: 16,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ],
                        ),
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.only(
                        left: 20,
                        right: 20,
                        bottom: 100,
                        top: 10,
                      ),
                      itemCount: musicVM.searchResults.length,
                      itemBuilder: (context, index) {
                        final track = musicVM.searchResults[index];
                        final isCurrent =
                            musicVM.currentTrack != null &&
                            musicVM.currentTrack!['trackId'] ==
                                track['trackId'];

                        return FadeInUp(
                          delay: Duration(milliseconds: 50 * (index % 10)),
                          duration: const Duration(milliseconds: 400),
                          child: Container(
                            margin: const EdgeInsets.only(bottom: 12),
                            decoration: BoxDecoration(
                              color: isCurrent
                                  ? const Color(0xFFFFF5F5)
                                  : Colors.white,
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(
                                color: isCurrent
                                    ? const Color(0xFFD32F2F).withOpacity(0.3)
                                    : Colors.transparent,
                              ),
                              boxShadow: [
                                BoxShadow(
                                  color: Colors.black.withOpacity(0.03),
                                  blurRadius: 10,
                                  offset: const Offset(0, 4),
                                ),
                              ],
                            ),
                            child: ListTile(
                              contentPadding: const EdgeInsets.symmetric(
                                horizontal: 12,
                                vertical: 4,
                              ),
                              leading: ClipRRect(
                                borderRadius: BorderRadius.circular(12),
                                child: Image.network(
                                  track['artworkUrl100'] ?? '',
                                  width: 50,
                                  height: 50,
                                  fit: BoxFit.cover,
                                  errorBuilder: (_, __, ___) => Container(
                                    width: 50,
                                    height: 50,
                                    color: Colors.grey.shade100,
                                    child: Icon(
                                      FluentIcons.music_note_1_24_regular,
                                      color: Colors.grey.shade400,
                                    ),
                                  ),
                                ),
                              ),
                              title: Text(
                                track['trackName'] ?? 'Không rõ',
                                style: TextStyle(
                                  fontWeight: isCurrent
                                      ? FontWeight.bold
                                      : FontWeight.w600,
                                  color: isCurrent
                                      ? const Color(0xFFD32F2F)
                                      : Colors.black87,
                                  fontSize: 15,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                              subtitle: Text(
                                track['artistName'] ?? '',
                                style: TextStyle(
                                  color: Colors.grey.shade600,
                                  fontSize: 13,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                              trailing: isCurrent && musicVM.isPlaying
                                  ? const Icon(
                                      FluentIcons.sound_wave_circle_24_filled,
                                      color: Color(0xFFD32F2F),
                                      size: 28,
                                    )
                                  : const Icon(
                                      FluentIcons.play_circle_24_regular,
                                      color: Colors.grey,
                                    ),
                              onTap: () => musicVM.playTrack(track, index),
                            ),
                          ),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}
