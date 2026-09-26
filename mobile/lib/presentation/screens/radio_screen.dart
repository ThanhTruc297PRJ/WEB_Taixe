import 'package:flutter/material.dart';
import 'package:just_audio/just_audio.dart';

class RadioStation {
  final String name;
  final String frequency;
  final String streamUrl;
  RadioStation({
    required this.name,
    required this.frequency,
    required this.streamUrl,
  });
}

class RadioScreen extends StatefulWidget {
  const RadioScreen({super.key});

  @override
  State<RadioScreen> createState() => _RadioScreenState();
}

class _RadioScreenState extends State<RadioScreen> {
  final AudioPlayer _audioPlayer = AudioPlayer();
  RadioStation? _currentStation;
  bool _isPlaying = false;
  bool _isLoading = false;

  final List<RadioStation> _stations = [
    RadioStation(
      name: 'VOV1 - Thời sự',
      frequency: 'FM 100 MHz',
      streamUrl: 'https://vov-live.admicro.vn/vov1.smil/playlist.m3u8',
    ),
    RadioStation(
      name: 'VOV3 - Âm nhạc',
      frequency: 'FM 102.7 MHz',
      streamUrl: 'https://vov-live.admicro.vn/vov3.smil/playlist.m3u8',
    ),
    RadioStation(
      name: 'VOH - Nhạc trẻ',
      frequency: 'FM 99.9 MHz',
      streamUrl: 'http://stream.voh.com.vn:8000/voh999',
    ),
    RadioStation(
      name: 'VOH - Giao thông',
      frequency: 'FM 95.6 MHz',
      streamUrl: 'http://stream.voh.com.vn:8000/voh956',
    ),
  ];

  @override
  void dispose() {
    _audioPlayer.dispose();
    super.dispose();
  }

  Future<void> _playStation(RadioStation station) async {
    try {
      if (_currentStation?.name == station.name) {
        if (_isPlaying) {
          await _audioPlayer.pause();
          setState(() => _isPlaying = false);
        } else {
          await _audioPlayer.play();
          setState(() => _isPlaying = true);
        }
        return;
      }

      setState(() {
        _currentStation = station;
        _isLoading = true;
        _isPlaying = false;
      });
      await _audioPlayer.setUrl(station.streamUrl);
      if (!mounted) return;
      setState(() {
        _isLoading = false;
        _isPlaying = true;
      });
      await _audioPlayer.play();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isLoading = false;
        _isPlaying = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Không thể kết nối đến kênh này')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      appBar: AppBar(
        title: const Text(
          'Radio FM',
          style: TextStyle(color: Colors.black87, fontWeight: FontWeight.bold),
        ),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black87),
      ),
      body: Column(
        children: [
          if (_currentStation != null)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: const BorderRadius.only(
                  bottomLeft: Radius.circular(32),
                  bottomRight: Radius.circular(32),
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.05),
                    blurRadius: 20,
                    offset: const Offset(0, 10),
                  ),
                ],
              ),
              child: Column(
                children: [
                  Container(
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      color: const Color(0xFF2A8B88).withValues(alpha: 0.1),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.radio,
                      size: 56,
                      color: Color(0xFF2A8B88),
                    ),
                  ),
                  const SizedBox(height: 24),
                  Text(
                    _currentStation!.name,
                    style: const TextStyle(
                      fontSize: 26,
                      fontWeight: FontWeight.w900,
                      color: Colors.black87,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _currentStation!.frequency,
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.grey.shade500,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 32),
                  if (_isLoading)
                    const CircularProgressIndicator(color: Color(0xFF2A8B88))
                  else
                    IconButton(
                      iconSize: 80,
                      icon: Icon(
                        _isPlaying
                            ? Icons.pause_circle_filled
                            : Icons.play_circle_fill,
                      ),
                      color: const Color(0xFF2A8B88),
                      onPressed: () => _playStation(_currentStation!),
                    ),
                ],
              ),
            ),
          const SizedBox(height: 16),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              itemCount: _stations.length,
              itemBuilder: (context, index) {
                final station = _stations[index];
                final isSelected = _currentStation?.name == station.name;

                return Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: isSelected
                          ? const Color(0xFF2A8B88).withValues(alpha: 0.3)
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
                      horizontal: 16,
                      vertical: 8,
                    ),
                    leading: CircleAvatar(
                      backgroundColor: isSelected
                          ? const Color(0xFF2A8B88).withValues(alpha: 0.15)
                          : Colors.grey.shade100,
                      child: Icon(
                        Icons.radio_outlined,
                        color: isSelected
                            ? const Color(0xFF2A8B88)
                            : Colors.grey.shade500,
                      ),
                    ),
                    title: Text(
                      station.name,
                      style: TextStyle(
                        fontWeight: isSelected
                            ? FontWeight.bold
                            : FontWeight.w600,
                        color: isSelected
                            ? const Color(0xFF2A8B88)
                            : Colors.black87,
                      ),
                    ),
                    subtitle: Text(
                      station.frequency,
                      style: TextStyle(color: Colors.grey.shade500),
                    ),
                    trailing: isSelected && _isPlaying
                        ? const Icon(
                            Icons.multitrack_audio,
                            color: Color(0xFF2A8B88),
                          )
                        : Icon(
                            Icons.play_arrow_outlined,
                            color: Colors.grey.shade400,
                          ),
                    onTap: () => _playStation(station),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
