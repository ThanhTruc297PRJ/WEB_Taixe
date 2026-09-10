import 'dart:async';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter_foreground_task/flutter_foreground_task.dart';
import 'package:google_mlkit_face_mesh_detection/google_mlkit_face_mesh_detection.dart';

import '../../data/models/event_log.dart';
import '../../data/repositories/event_log_repository.dart';
import '../../services/alert_service.dart';
import '../../services/camera/camera_frame_buffer.dart';
import '../../services/incident_api.dart';
import '../../services/ml/feature_window_aggregator.dart';
import '../../services/ml/landmark_feature_service.dart';
import '../../services/ml/tflite_model_service.dart';
import '../../services/monitoring/monitoring_task_handler.dart';

/// Model MLP-Feature dự đoán theo từng khung + làm mượt EMA, không còn giai
/// đoạn hiệu chỉnh baseline như model SVM cũ — chỉ còn idle / monitoring.
enum MonitoringPhase { idle, monitoring }

/// ViewModel điều phối camera + landmark + đặc trưng + model + cảnh báo + log.
///
/// Luồng mỗi khung (~6Hz): landmark -> 11 đặc trưng -> model -> EMA
/// (s = beta*s + (1-beta)*p) -> so threshold -> cảnh báo + ghi log.
class MonitoringViewModel extends ChangeNotifier {
  MonitoringViewModel({
    CameraFrameBuffer? cameraFrameBuffer,
    LandmarkFeatureService? landmarkFeatureService,
    TFLiteModelService? tfliteModelService,
    EventLogRepository? eventLogRepository,
    FeatureWindowAggregator? featureWindowAggregator,
    IncidentApi? incidentApi,
  })  : _cameraFrameBuffer = cameraFrameBuffer ?? CameraFrameBuffer(),
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

  // Sự cố: quay [_clipDuration] giây từ lúc phát hiện, tối đa 1 clip mỗi
  // [_incidentCooldown] (tài xế buồn ngủ liên tục không đẻ ra hàng loạt clip).
  static const _clipDuration = Duration(seconds: 10);
  static const _incidentCooldown = Duration(seconds: 60);
  DateTime? _lastIncidentAt;
  bool _capturingIncident = false;
  bool get capturingIncident => _capturingIncident;

  // ~6Hz: khớp EFF_FPS=6 (SAMPLE_INTERVAL=5 trên video 30fps) lúc train.
  static const _sampleInterval = Duration(milliseconds: 166);
  DateTime? _lastSampleAt;

  static const _statusMinInterval = Duration(milliseconds: 1000);
  DateTime? _lastStatusAt;

  // EMA state cho xác suất đầu ra.
  double? _smoothedProb;
  int _framesSinceFace = 0;

  MonitoringPhase phase = MonitoringPhase.idle;
  double? lastDrowsyProbability; // đã EMA
  List<EventLog> recentLogs = const [];

  bool get isMonitoring => phase != MonitoringPhase.idle;
  CameraFrameBuffer get cameraFrameBuffer => _cameraFrameBuffer;
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
    phase = MonitoringPhase.monitoring;

    try {
      await _cameraFrameBuffer.start(onFrame: _onFrame);
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

    await _cameraFrameBuffer.stop();
    await FlutterForegroundTask.stopService();

    _alertService.stopAlert();

    phase = MonitoringPhase.idle;
    lastDrowsyProbability = null;
    _smoothedProb = null;
    notifyListeners();
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
    _smoothedProb =
        _smoothedProb == null ? raw : beta * _smoothedProb! + (1 - beta) * raw;
    final probability = _smoothedProb!;
    lastDrowsyProbability = probability;
    notifyListeners();

    final threshold = _tfliteModelService.meta?.threshold ?? 0.5;
    final isDrowsy = probability >= threshold;

    _sendStatus(
      isDrowsy
          ? 'Cảnh báo: dấu hiệu buồn ngủ! (${(probability * 100).toStringAsFixed(0)}%)'
          : 'Trạng thái: bình thường (${(probability * 100).toStringAsFixed(0)}%)',
    );

    if (isDrowsy) {
      _alertService.playWarningAlert();

      final log = await _eventLogRepository.insert(
        EventLog(
          type: EventType.drowsiness,
          message: 'Model phát hiện dấu hiệu buồn ngủ',
          timestamp: now,
          confidence: probability,
        ),
      );
      recentLogs = [log, ...recentLogs].take(50).toList();
      notifyListeners();

      unawaited(_maybeCaptureIncident(probability, now));
    } else {
      _alertService.stopAlert();
    }
  }

  /// Quay 10s từ lúc phát hiện buồn ngủ rồi gửi lên backend. Chạy nền, không
  /// chặn vòng nhận diện; có cooldown để không gửi dồn dập.
  Future<void> _maybeCaptureIncident(double confidence, DateTime at) async {
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
      clipPath = await _cameraFrameBuffer.recordClip(_clipDuration);
    } catch (_) {
      clipPath = null;
    } finally {
      // Luôn bật lại stream để nhận diện tiếp, kể cả khi quay lỗi.
      try {
        await _cameraFrameBuffer.resumeStream(onFrame: _onFrame);
      } catch (_) {}
    }

    if (clipPath != null && phase == MonitoringPhase.monitoring) {
      try {
        await _incidentApi.reportDrowsiness(
          clip: File(clipPath),
          detectedAt: at,
          confidence: confidence,
        );
      } catch (_) {
        // best-effort: mất mạng thì bỏ qua, không làm phiền tài xế đang lái.
      }
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
    _cameraFrameBuffer.stop();
    _alertService.stopAlert();
    _landmarkFeatureService.dispose();
    _tfliteModelService.dispose();
    super.dispose();
  }
}
