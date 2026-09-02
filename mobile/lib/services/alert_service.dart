import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/foundation.dart';
import 'package:vibration/vibration.dart';

class AlertService {
  static final AlertService _instance = AlertService._internal();
  factory AlertService() => _instance;
  AlertService._internal();

  final AudioPlayer _audioPlayer = AudioPlayer();
  bool _isPlaying = false;

  Future<void> triggerDrowsinessAlert() async {
    if (_isPlaying) return;
    _isPlaying = true;

    try {
      await _audioPlayer.setReleaseMode(ReleaseMode.loop);
      await _audioPlayer.play(AssetSource('audio/alarm.mp3'));

      final hasVibrator = await Vibration.hasVibrator() ?? false;
      if (hasVibrator) {
        final hasCustom = await Vibration.hasCustomVibrationsSupport() ?? false;
        if (hasCustom) {
          Vibration.vibrate(pattern: [500, 1000, 500, 1000], repeat: 0);
        } else {
          Vibration.vibrate();
        }
      }
    } catch (e) {
      debugPrint('Lỗi phát chuông: $e');
    }
  }

  Future<void> stopAlert() async {
    if (!_isPlaying) return;
    _isPlaying = false;

    try {
      await _audioPlayer.stop();
      Vibration.cancel();
    } catch (e) {
      debugPrint('Lỗi tắt chuông: $e');
    }
  }

  void dispose() {
    _audioPlayer.dispose();
  }
}
