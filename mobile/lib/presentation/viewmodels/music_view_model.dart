import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:audioplayers/audioplayers.dart';

class MusicViewModel extends ChangeNotifier {
  final AudioPlayer _audioPlayer = AudioPlayer();

  List<dynamic> searchResults = [];
  bool isLoading = false;

  Map<String, dynamic>? currentTrack;
  int currentIndex = -1;
  bool isPlaying = false;
  bool showPopup = false; // Điều khiển việc hiện tai thỏ

  MusicViewModel() {
    _audioPlayer.onPlayerComplete.listen((_) {
      playNext(); // Hết bài tự chuyển bài tiếp theo
    });
  }

  Future<void> searchMusic(String query) async {
    if (query.trim().isEmpty) return;
    isLoading = true;
    notifyListeners();

    try {
      final url = Uri.parse(
        'https://itunes.apple.com/search?term=${Uri.encodeComponent(query)}&entity=song&limit=25',
      );
      final response = await http.get(url);
      if (response.statusCode == 200) {
        searchResults = json.decode(response.body)['results'];
      }
    } catch (e) {
      debugPrint('Lỗi tìm nhạc: $e');
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  Future<void> playTrack(Map<String, dynamic> track, int index) async {
    if (currentTrack != null && currentTrack!['trackId'] == track['trackId']) {
      togglePlayPause();
    } else {
      final url = track['previewUrl'];
      if (url != null) {
        await _audioPlayer.play(UrlSource(url));
        currentTrack = track;
        currentIndex = index;
        isPlaying = true;
        showPopup = true;
        notifyListeners();
      }
    }
  }

  void togglePlayPause() async {
    if (isPlaying) {
      await _audioPlayer.pause();
      isPlaying = false;
    } else {
      await _audioPlayer.resume();
      isPlaying = true;
    }
    notifyListeners();
  }

  void playNext() {
    if (searchResults.isNotEmpty && currentIndex < searchResults.length - 1) {
      playTrack(searchResults[currentIndex + 1], currentIndex + 1);
    }
  }

  void closePlayer() {
    _audioPlayer.stop();
    isPlaying = false;
    currentTrack = null;
    showPopup = false;
    notifyListeners();
  }

  @override
  void dispose() {
    _audioPlayer.dispose();
    super.dispose();
  }
}
