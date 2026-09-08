import 'package:audioplayers/audioplayers.dart';

class AlertService {
  static final AlertService _instance = AlertService._internal();
  factory AlertService() => _instance;
  AlertService._internal();

  final AudioPlayer _audioPlayer = AudioPlayer();
  bool _isPlaying = false;

  bool get isPlaying => _isPlaying;

  Future<void> playWarningAlert({String? customSoundUrl}) async {
    if (_isPlaying) return;

    try {
      _isPlaying = true;
      await _audioPlayer.stop();

      // Dùng asset đang có trong pubspec (assets/audio/alarm.mp3). File
      // sounds/alert_alarm.mp3 chưa được thêm vào assets.
      final soundSource = (customSoundUrl != null && customSoundUrl.isNotEmpty)
          ? UrlSource(customSoundUrl)
          : AssetSource('audio/alarm.mp3');

      await _audioPlayer.setReleaseMode(ReleaseMode.loop);
      await _audioPlayer.play(soundSource);
    } catch (e) {
      _isPlaying = false;
    }
  }

  Future<void> playQuickBeep() async {
    try {
      await _audioPlayer.stop();
      await _audioPlayer.setReleaseMode(ReleaseMode.stop);
      await _audioPlayer.play(AssetSource('sounds/short_beep.mp3'));
    } catch (_) {}
  }

  Future<void> stopAlert() async {
    if (!_isPlaying) return;
    try {
      await _audioPlayer.stop();
      _isPlaying = false;
    } catch (_) {
      _isPlaying = false;
    }
  }

  void dispose() {
    _audioPlayer.dispose();
  }
}
