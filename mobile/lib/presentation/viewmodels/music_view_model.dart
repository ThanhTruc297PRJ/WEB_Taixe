import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:http/http.dart' as http;
import 'package:file_picker/file_picker.dart';

class SongModel {
  final String id;
  final String title;
  final String artist;
  final String audioUrl;
  final String? artworkUrl;
  final bool isLocal;

  SongModel({
    required this.id,
    required this.title,
    required this.artist,
    required this.audioUrl,
    this.artworkUrl,
    this.isLocal = false,
  });
}

class MusicViewModel extends ChangeNotifier {
  final AudioPlayer _audioPlayer = AudioPlayer();

  SongModel? currentTrack;
  bool isPlaying = false;
  bool isLoading = false;

  List<SongModel> searchResults = [];
  final List<SongModel> favorites = [];
  final List<SongModel> history = [];

  MusicViewModel() {
    _audioPlayer.onPlayerComplete.listen((_) {
      isPlaying = false;
      notifyListeners();
    });
  }

  Future<void> searchMusic(String query) async {
    if (query.trim().isEmpty) return;
    isLoading = true;
    notifyListeners();

    try {
      final url = Uri.parse(
        'https://itunes.apple.com/search?term=${Uri.encodeComponent(query)}&media=music&limit=25',
      );
      final response = await http.get(url);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final List results = data['results'];
        searchResults = results
            .where((item) => item['previewUrl'] != null)
            .map(
              (item) => SongModel(
                id: item['trackId'].toString(),
                title: item['trackName'] ?? 'Không rõ tiêu đề',
                artist: item['artistName'] ?? 'Không rõ ca sĩ',
                audioUrl: item['previewUrl'],
                artworkUrl: item['artworkUrl100'],
                isLocal: false,
              ),
            )
            .toList();
      }
    } catch (_) {
      searchResults = [];
    }

    isLoading = false;
    notifyListeners();
  }

  void clearSearch() {
    searchResults.clear();
    notifyListeners();
  }

  Future<void> pickLocalAudioFile() async {
    try {
      FilePickerResult? result = await FilePicker.pickFiles(
        type: FileType.audio,
      );

      if (result != null && result.files.single.path != null) {
        final file = result.files.single;
        final localSong = SongModel(
          id: 'local_${DateTime.now().millisecondsSinceEpoch}',
          title: file.name.replaceAll('.mp3', ''),
          artist: 'Bộ nhớ thiết bị',
          audioUrl: file.path!,
          isLocal: true,
        );
        playTrack(localSong);
      }
    } catch (_) {}
  }

  Future<void> playTrack(SongModel track) async {
    if (currentTrack?.id == track.id) {
      togglePlayPause();
      return;
    }

    currentTrack = track;
    history.removeWhere((item) => item.id == track.id);
    history.insert(0, track);

    await _audioPlayer.stop();
    if (track.isLocal) {
      await _audioPlayer.play(DeviceFileSource(track.audioUrl));
    } else {
      await _audioPlayer.play(UrlSource(track.audioUrl));
    }
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

  bool isFavorite(String songId) {
    return favorites.any((item) => item.id == songId);
  }

  void toggleFavorite(SongModel track) {
    if (isFavorite(track.id)) {
      favorites.removeWhere((item) => item.id == track.id);
    } else {
      favorites.add(track);
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
