import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/material.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Radio API Test',
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple)),
      home: const RadioTestPage(),
    );
  }
}

enum _PlayState { stopped, loading, playing, paused, error }

class RadioTestPage extends StatefulWidget {
  const RadioTestPage({super.key});

  @override
  State<RadioTestPage> createState() => _RadioTestPageState();
}

class _RadioTestPageState extends State<RadioTestPage> {
  final _urlController = TextEditingController(
    text: 'https://ice1.somafm.com/groovesalad-256-mp3',
  );
  final _player = AudioPlayer();

  _PlayState _state = _PlayState.stopped;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _player.onPlayerStateChanged.listen((s) {
      if (!mounted) return;
      setState(() {
        switch (s) {
          case PlayerState.playing:
            _state = _PlayState.playing;
          case PlayerState.paused:
            _state = _PlayState.paused;
          case PlayerState.stopped:
          case PlayerState.completed:
            _state = _PlayState.stopped;
          case PlayerState.disposed:
            break;
        }
      });
    });
  }

  @override
  void dispose() {
    _player.dispose();
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _play() async {
    final url = _urlController.text.trim();
    if (url.isEmpty) return;

    setState(() {
      _state = _PlayState.loading;
      _errorMessage = null;
    });

    try {
      await _player.play(UrlSource(url));
      if (!mounted) return;
      setState(() => _state = _PlayState.playing);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _state = _PlayState.error;
        _errorMessage = e.toString();
      });
    }
  }

  Future<void> _pause() async {
    await _player.pause();
  }

  Future<void> _stop() async {
    await _player.stop();
    if (!mounted) return;
    setState(() => _state = _PlayState.stopped);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Test Radio Stream')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _urlController,
              keyboardType: TextInputType.url,
              decoration: const InputDecoration(
                labelText: 'URL API / stream radio',
                hintText: 'https://.../stream.mp3',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _state == _PlayState.loading ? null : _play,
                    icon: const Icon(Icons.play_arrow),
                    label: const Text('Play'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _state == _PlayState.playing ? _pause : null,
                    icon: const Icon(Icons.pause),
                    label: const Text('Pause'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _state == _PlayState.stopped ? null : _stop,
                    icon: const Icon(Icons.stop),
                    label: const Text('Stop'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),
            _StatusCard(state: _state, errorMessage: _errorMessage),
          ],
        ),
      ),
    );
  }
}

class _StatusCard extends StatelessWidget {
  const _StatusCard({required this.state, required this.errorMessage});

  final _PlayState state;
  final String? errorMessage;

  @override
  Widget build(BuildContext context) {
    final (icon, color, label) = switch (state) {
      _PlayState.stopped => (Icons.stop_circle_outlined, Colors.grey, 'Đã dừng'),
      _PlayState.loading => (Icons.hourglass_top, Colors.orange, 'Đang kết nối...'),
      _PlayState.playing => (Icons.graphic_eq, Colors.green, 'Đang phát'),
      _PlayState.paused => (Icons.pause_circle_outline, Colors.blue, 'Tạm dừng'),
      _PlayState.error => (Icons.error_outline, Colors.red, 'Lỗi'),
    };

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: color),
                const SizedBox(width: 8),
                Text(label, style: Theme.of(context).textTheme.titleMedium),
              ],
            ),
            if (errorMessage != null) ...[
              const SizedBox(height: 8),
              Text(
                errorMessage!,
                style: TextStyle(color: Colors.red.shade700, fontSize: 12),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
