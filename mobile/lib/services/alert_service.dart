import 'package:audioplayers/audioplayers.dart';
import 'package:vibration/vibration.dart';

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

  /// Mức nhắc nhẹ: rung 2 nhịp + chuông 1 lần (không lặp), không làm phiền
  /// như báo động.
  Future<void> playReminder() async {
    try {
      if (await Vibration.hasVibrator()) {
        Vibration.vibrate(pattern: [0, 300, 150, 300]);
      }
    } catch (_) {}
    if (_isPlaying) return; // đang báo động thì thôi
    try {
      await _audioPlayer.stop();
      await _audioPlayer.setReleaseMode(ReleaseMode.stop);
      await _audioPlayer.play(AssetSource('audio/alarm.mp3'), volume: 0.6);
    } catch (_) {}
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
