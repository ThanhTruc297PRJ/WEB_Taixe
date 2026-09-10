import 'package:flutter/material.dart';
import 'package:audioplayers/audioplayers.dart';

import '../../services/api_client.dart';
import '../../services/driver_music_api.dart';

class SongModel {
  final String id;
  final String title;
  final String artist;
  final String audioUrl;
  final String? artworkUrl;

  SongModel({
    required this.id,
    required this.title,
    required this.artist,
    required this.audioUrl,
    this.artworkUrl,
  });

  factory SongModel.fromJson(Map<String, dynamic> j) => SongModel(
        id: j['id'].toString(),
        title: (j['title'] ?? 'Không rõ tiêu đề').toString(),
        artist: (j['artist'] ?? 'Không rõ ca sĩ').toString(),
        audioUrl: (j['audioUrl'] ?? '').toString(),
        artworkUrl: j['artworkUrl']?.toString(),
      );
}

class MusicViewModel extends ChangeNotifier {
  MusicViewModel({DriverMusicApi? api})
      : _api = api ?? DriverMusicApi() {
    _audioPlayer.onPlayerComplete.listen((_) {
      isPlaying = false;
      notifyListeners();
    });
  }

  final AudioPlayer _audioPlayer = AudioPlayer();
  final DriverMusicApi _api;

  SongModel? currentTrack;
  bool isPlaying = false;
  bool isLoading = false;

  /// Thông báo ngắn hiển thị cho tài xế (bài bị admin tắt, lỗi mạng...).
  String? notice;

  List<SongModel> searchResults = [];
  final List<SongModel> favorites = [];
  final List<SongModel> history = [];

  void clearNotice() {
    notice = null;
    notifyListeners();
  }

  Future<void> searchMusic(String query) async {
    if (query.trim().isEmpty) return;
    isLoading = true;
    notice = null;
    notifyListeners();

    try {
      final items = await _api.search(query);
      searchResults = items.map(SongModel.fromJson).toList();
      if (searchResults.isEmpty) notice = 'Không tìm thấy bài hát phù hợp';
    } on ApiException catch (e) {
      searchResults = [];
      notice = e.message;
    } catch (_) {
      searchResults = [];
      notice = 'Không kết nối được máy chủ nhạc';
    }

    isLoading = false;
    notifyListeners();
  }

  void clearSearch() {
    searchResults.clear();
    notifyListeners();
  }

  Future<void> playTrack(SongModel track) async {
    if (currentTrack?.id == track.id) {
      togglePlayPause();
      return;
    }

    // Xin phép backend trước — bài có thể đã bị admin tắt sau khi tài xế tìm.
    try {
      await _api.registerPlay(track.id);
    } on ApiException catch (e) {
      notice = e.statusCode == 403
          ? 'Bài này đã bị quản trị viên tắt'
          : e.message;
      favorites.removeWhere((s) => s.id == track.id);
      searchResults.removeWhere((s) => s.id == track.id);
      history.removeWhere((s) => s.id == track.id);
      notifyListeners();
      return;
    } catch (_) {
      notice = 'Không kết nối được máy chủ nhạc';
      notifyListeners();
      return;
    }

    currentTrack = track;
    history.removeWhere((item) => item.id == track.id);
    history.insert(0, track);

    await _audioPlayer.stop();
    await _audioPlayer.play(UrlSource(track.audioUrl));
    isPlaying = true;
    notifyListeners();
  }

  void togglePlayPause() async {
    if (isPlaying) {
      await _audioPlayer.pause();
      isPlaying = false;
    } else if (currentTrack != null) {
      await _audioPlayer.resume();
      isPlaying = true;
    }
    notifyListeners();
  }

  bool isFavorite(String songId) => favorites.any((item) => item.id == songId);

  void toggleFavorite(SongModel track) {
    if (isFavorite(track.id)) {
      favorites.removeWhere((item) => item.id == track.id);
    } else {
      favorites.add(track);
    }
    notifyListeners();
  }

  Future<void> reportTrack(SongModel track, {String? reason}) async {
    try {
      await _api.report(track.id, reason);
      notice = 'Đã gửi báo cáo. Cảm ơn bạn.';
    } on ApiException catch (e) {
      notice = e.message;
    } catch (_) {
      notice = 'Không gửi được báo cáo';
    }
    notifyListeners();
  }

  void closePlayer() {
    _audioPlayer.stop();
    isPlaying = false;
    currentTrack = null;
    notifyListeners();
  }

  @override
  void dispose() {
    _audioPlayer.dispose();
    super.dispose();
  }
}
