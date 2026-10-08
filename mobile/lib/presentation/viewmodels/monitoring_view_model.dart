import 'dart:async';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter_foreground_task/flutter_foreground_task.dart';
import 'package:google_mlkit_face_mesh_detection/google_mlkit_face_mesh_detection.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../data/models/event_log.dart';
import '../../data/repositories/event_log_repository.dart';
import '../../services/alert_service.dart';
import '../../services/camera/camera_frame_buffer.dart';
import '../../services/camera/frame_source.dart';
import '../../services/camera/network_frame_source.dart';
import '../../services/incident_api.dart';
import '../../services/ml/fatigue_scorer.dart';
import '../../services/ml/feature_window_aggregator.dart';
import '../../services/ml/landmark_feature_service.dart';
import '../../services/ml/tflite_model_service.dart';
import '../../services/monitoring/monitoring_task_handler.dart';

enum MonitoringPhase { idle, monitoring }

class MonitoringViewModel extends ChangeNotifier {
  MonitoringViewModel({
    CameraFrameBuffer? cameraFrameBuffer,
    LandmarkFeatureService? landmarkFeatureService,
    TFLiteModelService? tfliteModelService,
    EventLogRepository? eventLogRepository,
    FeatureWindowAggregator? featureWindowAggregator,
    IncidentApi? incidentApi,
  }) : _cameraFrameBuffer = cameraFrameBuffer ?? CameraFrameBuffer(),
       _landmarkFeatureService =
           landmarkFeatureService ?? LandmarkFeatureService(),
       _tfliteModelService = tfliteModelService ?? TFLiteModelService(),
       _eventLogRepository = eventLogRepository ?? EventLogRepository(),
       _featureWindowAggregator =
           featureWindowAggregator ?? FeatureWindowAggregator(),
       _incidentApi = incidentApi ?? IncidentApi();

  final CameraFrameBuffer _cameraFrameBuffer;
  final LandmarkFeatureService _landmarkFeatureService;
  final TFLiteModelService _tfliteModelService;
  final EventLogRepository _eventLogRepository;
  final FeatureWindowAggregator _featureWindowAggregator;
  final IncidentApi _incidentApi;

  final AlertService _alertService = AlertService();

  static const _clipDuration = Duration(seconds: 10);
  static const _incidentCooldown = Duration(seconds: 60);
  DateTime? _lastIncidentAt;
  bool _capturingIncident = false;
  bool get capturingIncident => _capturingIncident;

  static const _sampleInterval = Duration(milliseconds: 166);
  DateTime? _lastSampleAt;

  static const _statusMinInterval = Duration(milliseconds: 1000);
  DateTime? _lastStatusAt;

  double? _smoothedProb;
  int _framesSinceFace = 0;

  /// Cộng dồn điểm mệt mỏi theo sự kiện — quyết định khi nào nhắc / báo động.
  final FatigueScorer _fatigueScorer = FatigueScorer();
  double fatigueScore = 0;
  FatigueLevel get fatigueLevel =>
      _alarmRinging ? FatigueLevel.alarm : _fatigueScorer.level;
  double get fatigueReminderScore => _fatigueScorer.config.reminderScore;
  double get fatigueAlarmScore => _fatigueScorer.config.alarmScore;

  /// Chuông báo động đang kêu: tắt khi tài xế bấm tắt, hoặc mở mắt tỉnh táo
  /// liên tục [_alarmStopAfterAlert].
  bool _alarmRinging = false;
  bool get alarmRinging => _alarmRinging;
  static const _alarmStopAfterAlert = Duration(seconds: 5);

  MonitoringPhase phase = MonitoringPhase.idle;
  double? lastDrowsyProbability;
  List<EventLog> recentLogs = const [];

  bool get isMonitoring => phase != MonitoringPhase.idle;
  CameraFrameBuffer get cameraFrameBuffer => _cameraFrameBuffer;

  // ── Nguồn hình: camera điện thoại hoặc camera ngoài qua đường dẫn ──────
  static const _prefUseExternal = 'camera_use_external';
  static const _prefExternalUrl = 'camera_external_url';
  bool useExternalCamera = false;
  String externalCameraUrl = '';
  NetworkFrameSource? _networkSource;
  late FrameSource _source = _cameraFrameBuffer;

  /// Đang giám sát bằng camera ngoài (để màn hình hiện ảnh từ luồng mạng).
  NetworkFrameSource? get networkSource =>
      _source is NetworkFrameSource ? _source as NetworkFrameSource : null;

  Future<void> loadCameraSettings() async {
    final prefs = await SharedPreferences.getInstance();
    useExternalCamera = prefs.getBool(_prefUseExternal) ?? false;
    externalCameraUrl = prefs.getString(_prefExternalUrl) ?? '';
    notifyListeners();
  }

  Future<void> setCameraSource({required bool external, String? url}) async {
    if (isMonitoring) return;
    useExternalCamera = external;
    if (url != null) externalCameraUrl = NetworkFrameSource.normalize(url);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_prefUseExternal, useExternalCamera);
    await prefs.setString(_prefExternalUrl, externalCameraUrl);
    notifyListeners();
  }

  double get drowsyThreshold => _tfliteModelService.meta?.threshold ?? 0.5;

  void initForegroundTask() {
    FlutterForegroundTask.init(
      androidNotificationOptions: AndroidNotificationOptions(
        channelId: 'driver_monitoring_service',
        channelName: 'Giám sát an toàn lái xe',
        channelDescription:
            'Thông báo khi ứng dụng đang giám sát trạng thái tài xế.',
        onlyAlertOnce: true,
      ),
      iosNotificationOptions: const IOSNotificationOptions(),
      foregroundTaskOptions: ForegroundTaskOptions(
        eventAction: ForegroundTaskEventAction.repeat(5000),
        autoRunOnBoot: false,
        allowWakeLock: true,
        allowWifiLock: false,
      ),
    );
  }

  Future<void> start() async {
    if (isMonitoring) return;

    if (!_tfliteModelService.isLoaded) {
      await _tfliteModelService.load();
    }

    if (await FlutterForegroundTask.isRunningService) {
      await FlutterForegroundTask.restartService();
    } else {
      await FlutterForegroundTask.startService(
        serviceId: 100,
        notificationTitle: 'Đang giám sát an toàn lái xe',
        notificationText: 'Đang phân tích...',
        callback: monitoringTaskCallback,
      );
    }

    _featureWindowAggregator.reset();
    _smoothedProb = null;
    _framesSinceFace = 0;
    _lastIncidentAt = null;
    lastDrowsyProbability = null;
    final meta = _tfliteModelService.meta;
    _fatigueScorer
      ..config = FatigueConfig.fromJson(
        meta?.fatigue,
        earClosed: meta?.earBlinkThreshold,
      )
      ..reset();
    fatigueScore = 0;
    _alarmRinging = false;
    phase = MonitoringPhase.monitoring;

    if (useExternalCamera && externalCameraUrl.isNotEmpty) {
      _networkSource = NetworkFrameSource(externalCameraUrl);
      _source = _networkSource!;
    } else {
      _source = _cameraFrameBuffer;
    }

    try {
      await _source.start(onFrame: _onFrame);
    } catch (_) {
      phase = MonitoringPhase.idle;
      await FlutterForegroundTask.stopService();
      notifyListeners();
      rethrow;
    }

    notifyListeners();
  }

  Future<void> stop() async {
    if (!isMonitoring) return;

    await _source.stop();
    await FlutterForegroundTask.stopService();

    _alertService.stopAlert();

    phase = MonitoringPhase.idle;
    lastDrowsyProbability = null;
    _smoothedProb = null;
    _fatigueScorer.reset();
    fatigueScore = 0;
    _alarmRinging = false;
    notifyListeners();
  }

  // Hàm được gọi khi bấm nút "Tắt chuông cảnh báo"
  void stopAlarm() {
    _alarmRinging = false;
    _alertService.stopAlert();
    notifyListeners();
  }

  Future<void> switchCamera() async {
    if (!isMonitoring) return;
    try {
      await _source.switchCamera(onFrame: _onFrame);
      notifyListeners();
    } catch (e) {
      debugPrint('Lỗi chuyển camera: $e');
    }
  }

  void _sendStatus(String text) {
    final now = DateTime.now();
    if (_lastStatusAt != null &&
        now.difference(_lastStatusAt!) < _statusMinInterval) {
      return;
    }
    _lastStatusAt = now;
    FlutterForegroundTask.sendDataToTask(text);
  }

  void _onFrame(InputImage image) {
    final now = DateTime.now();
    if (_lastSampleAt != null &&
        now.difference(_lastSampleAt!) < _sampleInterval) {
      return;
    }
    _lastSampleAt = now;
    _processFrame(image, now);
  }

  Future<void> _processFrame(InputImage image, DateTime now) async {
    if (phase != MonitoringPhase.monitoring) return;

    final signal = await _landmarkFeatureService.analyze(image);

    if (signal == null) {
      _framesSinceFace++;
      final gapReset = _tfliteModelService.meta?.emaGapReset ?? 20;
      if (_framesSinceFace > gapReset) {
        _smoothedProb = null;
        _featureWindowAggregator.reset();
        // Mất mặt ngắn (gục đầu, quay gương) vẫn giữ lần nhắm mắt đang đếm —
        // gục đầu khi đang nhắm mắt chính là dấu hiệu ngủ gật.
        _fatigueScorer.faceLost();
      }
      _sendStatus('Không phát hiện khuôn mặt');
      return;
    }
    _framesSinceFace = 0;

    if (!_tfliteModelService.isLoaded) {
      _sendStatus('Model chưa sẵn sàng');
      return;
    }

    final features = _featureWindowAggregator.addSample(signal);
    final raw = _tfliteModelService.predictDrowsyProbability(features);

    final beta = _tfliteModelService.meta?.emaBeta ?? 0.7;
    _smoothedProb = _smoothedProb == null
        ? raw
        : beta * _smoothedProb! + (1 - beta) * raw;
    final probability = _smoothedProb!;
    lastDrowsyProbability = probability;
    notifyListeners();

    // Model KHÔNG còn trực tiếp bật chuông: chỉ là 1 nguồn góp điểm mệt mỏi.
    // Chuông chỉ kêu khi điểm cộng dồn đủ ngưỡng, hoặc nhắm mắt liền quá lâu.
    final threshold = _tfliteModelService.meta?.threshold ?? 0.5;
    final update = _fatigueScorer.update(
      now: now,
      ear: signal.ear,
      mar: signal.mar,
      tilt: signal.tilt,
      modelProbability: probability,
      modelThreshold: threshold,
    );
    fatigueScore = update.score;

    for (final event in update.events) {
      await _log(
        '${event.label} (${(event.duration.inMilliseconds / 1000).toStringAsFixed(1)} giây) · +${event.points.toStringAsFixed(0)} điểm',
        now,
        probability,
      );
    }

    if (update.enteredAlarm) {
      final summary = _fatigueScorer.summary();
      final reason = update.immediate
          ? 'Nhắm mắt liên tục quá lâu'
          : 'Điểm mệt mỏi ${update.score.toStringAsFixed(0)}/100';
      _alarmRinging = true;
      _alertService.playWarningAlert();
      await _log('BÁO ĐỘNG: $reason', now, probability);
      // Hạ điểm ngay để không báo liên tục; chuông vẫn kêu tới khi tài xế
      // tỉnh táo trở lại hoặc bấm tắt.
      _fatigueScorer.acknowledgeAlarm();
      fatigueScore = _fatigueScorer.score;
      unawaited(
        _maybeCaptureIncident(
          probability,
          now,
          note: [reason, if (summary.isNotEmpty) summary].join(' — '),
        ),
      );
    } else if (update.enteredReminder) {
      _alertService.playReminder();
      await _log('Nhắc nhẹ: bạn có dấu hiệu mệt mỏi', now, probability);
    }

    if (_alarmRinging) {
      final openFor = _fatigueScorer.eyesOpenFor(now);
      if (openFor != null && openFor >= _alarmStopAfterAlert) {
        _alarmRinging = false;
        _alertService.stopAlert();
      }
    }

    _sendStatus(switch (fatigueLevel) {
      FatigueLevel.alarm => 'BÁO ĐỘNG: dấu hiệu ngủ gật!',
      FatigueLevel.reminder =>
        'Có dấu hiệu mệt mỏi (${fatigueScore.toStringAsFixed(0)}/100) — nên dừng nghỉ',
      FatigueLevel.normal =>
        'Tỉnh táo · điểm mệt mỏi ${fatigueScore.toStringAsFixed(0)}/100',
    });
    notifyListeners();
  }

  /// Chỉ ghi log khi có SỰ KIỆN (nhắm lâu, ngáp, báo động...), không ghi mỗi khung.
  Future<void> _log(String message, DateTime at, double confidence) async {
    final log = await _eventLogRepository.insert(
      EventLog(
        type: EventType.drowsiness,
        message: message,
        timestamp: at,
        confidence: confidence,
      ),
    );
    recentLogs = [log, ...recentLogs].take(50).toList();
  }

  Future<void> _maybeCaptureIncident(
    double confidence,
    DateTime at, {
    String? note,
  }) async {
    if (_capturingIncident) return;
    if (_lastIncidentAt != null &&
        at.difference(_lastIncidentAt!) < _incidentCooldown) {
      return;
    }
    _capturingIncident = true;
    _lastIncidentAt = at;
    notifyListeners();

    String? clipPath;
    try {
      _sendStatus('Đang ghi lại video sự cố...');
      clipPath = await _source.recordClip(_clipDuration);
    } catch (_) {
      clipPath = null;
    } finally {
      try {
        await _source.resumeStream(onFrame: _onFrame);
      } catch (_) {}
    }

    if (clipPath != null && phase == MonitoringPhase.monitoring) {
      try {
        await _incidentApi.reportDrowsiness(
          clip: File(clipPath),
          detectedAt: at,
          confidence: confidence,
          note: note,
          source: _source.isExternal ? 'external' : 'phone',
        );
      } catch (_) {}
    }
    try {
      if (clipPath != null) {
        final f = File(clipPath);
        if (await f.exists()) await f.delete();
      }
    } catch (_) {}

    _capturingIncident = false;
    notifyListeners();
  }

  Future<void> loadRecentLogs() async {
    recentLogs = await _eventLogRepository.recent();
    notifyListeners();
  }

  @override
  void dispose() {
    _source.stop();
    _alertService.stopAlert();
    _landmarkFeatureService.dispose();
    _tfliteModelService.dispose();
    super.dispose();
  }
}
