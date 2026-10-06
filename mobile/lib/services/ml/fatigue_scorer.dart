import 'dart:math';

/// Mức phản ứng theo điểm mệt mỏi.
enum FatigueLevel {
  /// Bình thường — chỉ hiển thị thanh điểm.
  normal,

  /// Nhắc nhẹ (rung + chuông 1 lần), KHÔNG gửi sự cố.
  reminder,

  /// Cảnh báo mạnh: chuông liên tục + quay clip + gửi 1 sự cố lên server.
  alarm,
}

enum FatigueEventKind { longClosure, microsleep, yawn, headDrop, modelDrowsy }

class FatigueEvent {
  const FatigueEvent(this.kind, this.points, this.duration);

  final FatigueEventKind kind;
  final double points;
  final Duration duration;

  String get label => switch (kind) {
    FatigueEventKind.longClosure => 'Nhắm mắt lâu',
    FatigueEventKind.microsleep => 'Ngủ gật chớp nhoáng',
    FatigueEventKind.yawn => 'Ngáp',
    FatigueEventKind.headDrop => 'Gục / nghiêng đầu',
    FatigueEventKind.modelDrowsy => 'AI nhận diện buồn ngủ',
  };
}

/// Tham số chấm điểm — giá trị khởi đầu, chỉnh qua `fatigue` trong
/// assets/models/model_meta.json (không cần sửa code). Cần chạy thử với tài
/// xế thật để cân giữa báo nhầm và bỏ sót.
class FatigueConfig {
  const FatigueConfig({
    this.earClosed = 0.21,
    this.blinkMax = const Duration(milliseconds: 400),
    this.longClosureMin = const Duration(milliseconds: 500),
    this.microsleepMin = const Duration(milliseconds: 1500),
    this.immediateAlarmClosure = const Duration(seconds: 2),
    this.longClosurePoints = 10,
    this.microsleepPoints = 25,
    this.yawnMar = 0.6,
    this.yawnMin = const Duration(seconds: 1),
    this.yawnPoints = 5,
    this.headDropDegrees = 20,
    this.headDropMin = const Duration(milliseconds: 1500),
    this.headDropPoints = 5,
    this.modelPointsPerSecond = 2,
    this.decayPerSecond = 0.2,
    this.reminderScore = 30,
    this.alarmScore = 60,
    this.maxScore = 100,
    this.scoreAfterAlarm = 30,
  });

  /// EAR dưới ngưỡng này coi là mắt nhắm (khớp ear_blink_thresh lúc train).
  final double earClosed;

  /// Nhắm ngắn hơn = chớp mắt bình thường, không tính điểm.
  final Duration blinkMax;
  final Duration longClosureMin;
  final Duration microsleepMin;

  /// Nhắm LIÊN TỤC tới mức này -> báo chuông ngay, không chờ cộng đủ điểm
  /// (60 km/h x 2 giây = ~33 m xe chạy không người lái).
  final Duration immediateAlarmClosure;

  final double longClosurePoints;
  final double microsleepPoints;
  final double yawnMar;
  final Duration yawnMin;
  final double yawnPoints;

  /// Đầu nghiêng lệch khỏi tư thế quen của tài xế quá số độ này đủ lâu.
  final double headDropDegrees;
  final Duration headDropMin;
  final double headDropPoints;

  /// Mỗi giây model (đã làm mượt) báo buồn ngủ.
  final double modelPointsPerSecond;

  /// Điểm tự giảm mỗi giây khi tỉnh táo (0.2 = 2 điểm / 10 giây).
  final double decayPerSecond;

  final double reminderScore;
  final double alarmScore;
  final double maxScore;

  /// Sau khi đã báo động mạnh + gửi sự cố, điểm hạ về mức này.
  final double scoreAfterAlarm;

  factory FatigueConfig.fromJson(Map<String, dynamic>? j, {double? earClosed}) {
    const d = FatigueConfig();
    if (j == null) return FatigueConfig(earClosed: earClosed ?? d.earClosed);
    double n(String k, double fallback) =>
        (j[k] as num?)?.toDouble() ?? fallback;
    Duration ms(String k, Duration fallback) =>
        j[k] is num ? Duration(milliseconds: (j[k] as num).toInt()) : fallback;
    return FatigueConfig(
      earClosed: earClosed ?? d.earClosed,
      blinkMax: ms('blink_max_ms', d.blinkMax),
      longClosureMin: ms('long_closure_min_ms', d.longClosureMin),
      microsleepMin: ms('microsleep_min_ms', d.microsleepMin),
      immediateAlarmClosure: ms(
        'immediate_alarm_closure_ms',
        d.immediateAlarmClosure,
      ),
      longClosurePoints: n('long_closure_points', d.longClosurePoints),
      microsleepPoints: n('microsleep_points', d.microsleepPoints),
      yawnMar: n('yawn_mar', d.yawnMar),
      yawnMin: ms('yawn_min_ms', d.yawnMin),
      yawnPoints: n('yawn_points', d.yawnPoints),
      headDropDegrees: n('head_drop_degrees', d.headDropDegrees),
      headDropMin: ms('head_drop_min_ms', d.headDropMin),
      headDropPoints: n('head_drop_points', d.headDropPoints),
      modelPointsPerSecond: n(
        'model_points_per_second',
        d.modelPointsPerSecond,
      ),
      decayPerSecond: n('decay_per_second', d.decayPerSecond),
      reminderScore: n('reminder_score', d.reminderScore),
      alarmScore: n('alarm_score', d.alarmScore),
      maxScore: n('max_score', d.maxScore),
      scoreAfterAlarm: n('score_after_alarm', d.scoreAfterAlarm),
    );
  }
}

/// Kết quả sau mỗi khung hình.
class FatigueUpdate {
  const FatigueUpdate({
    required this.score,
    required this.level,
    required this.events,
    required this.enteredReminder,
    required this.enteredAlarm,
    required this.immediate,
  });

  /// Điểm mệt mỏi hiện tại (0..maxScore).
  final double score;
  final FatigueLevel level;

  /// Sự kiện vừa kết thúc ở khung này (để ghi log) — thường rỗng.
  final List<FatigueEvent> events;

  /// Vừa chuyển lên mức nhắc nhẹ / báo động ở khung này (để phát âm 1 lần).
  final bool enteredReminder;
  final bool enteredAlarm;

  /// Báo động do nhắm mắt liên tục quá lâu (không phải do cộng đủ điểm).
  final bool immediate;
}

/// Cộng dồn "điểm mệt mỏi" theo SỰ KIỆN thay vì báo động theo từng khung hình.
///
/// Chớp mắt bình thường không tính; nhắm mắt lâu, ngủ gật chớp nhoáng, ngáp,
/// gục đầu và các giây model báo buồn ngủ cộng điểm; tỉnh táo thì điểm tự
/// giảm. Đạt [FatigueConfig.reminderScore] -> nhắc nhẹ, đạt
/// [FatigueConfig.alarmScore] -> báo động. Riêng nhắm mắt liên tục quá
/// [FatigueConfig.immediateAlarmClosure] -> báo động ngay.
///
/// Tính theo thời gian thật (không theo số khung) nên không phụ thuộc tốc
/// độ lấy mẫu camera.
class FatigueScorer {
  FatigueScorer([FatigueConfig? config])
    : config = config ?? const FatigueConfig();

  FatigueConfig config;

  double _score = 0;
  FatigueLevel _level = FatigueLevel.normal;
  DateTime? _lastAt;

  DateTime? _closedSince;
  bool _immediateFired = false;
  DateTime? _yawnSince;
  DateTime? _tiltSince;
  bool _tiltCounted = false;
  double? _tiltBaseline;
  double _modelSeconds = 0;

  /// Đếm sự kiện từ lần báo động gần nhất — gửi kèm sự cố cho admin xem.
  final Map<FatigueEventKind, int> _counts = {};

  double get score => _score;
  FatigueLevel get level => _level;

  /// Mắt đang mở liên tục được bao lâu (null = đang nhắm).
  Duration? eyesOpenFor(DateTime now) =>
      _closedSince == null && _lastOpenSince != null
      ? now.difference(_lastOpenSince!)
      : null;
  DateTime? _lastOpenSince;

  void reset() {
    _score = 0;
    _level = FatigueLevel.normal;
    _lastAt = null;
    _closedSince = null;
    _immediateFired = false;
    _yawnSince = null;
    _tiltSince = null;
    _tiltCounted = false;
    _tiltBaseline = null;
    _modelSeconds = 0;
    _lastOpenSince = null;
    _counts.clear();
  }

  /// Mất khuôn mặt: bỏ dở các sự kiện đang theo dõi (không cộng điểm cho
  /// lần nhắm bị cắt ngang), giữ nguyên điểm đã tích.
  void faceLost() {
    _closedSince = null;
    _immediateFired = false;
    _yawnSince = null;
    _tiltSince = null;
    _tiltCounted = false;
    _lastAt = null;
    _lastOpenSince = null;
  }

  /// Gọi sau khi đã báo động + gửi sự cố: hạ điểm để không báo liên tục.
  void acknowledgeAlarm() {
    _score = min(_score, config.scoreAfterAlarm);
    _level = _levelFor(_score);
    _counts.clear();
  }

  /// Tóm tắt sự kiện từ lần báo động trước, VD "2 lần nhắm mắt lâu, 1 lần ngáp".
  String summary() {
    if (_counts.isEmpty) return '';
    const names = {
      FatigueEventKind.longClosure: 'nhắm mắt lâu',
      FatigueEventKind.microsleep: 'ngủ gật chớp nhoáng',
      FatigueEventKind.yawn: 'ngáp',
      FatigueEventKind.headDrop: 'gục/nghiêng đầu',
      FatigueEventKind.modelDrowsy: 'giây AI báo buồn ngủ',
    };
    return _counts.entries
        .map((e) => '${e.value} lần ${names[e.key]}')
        .join(', ')
        .replaceAll('lần giây', 'giây');
  }

  FatigueUpdate update({
    required DateTime now,
    required double ear,
    required double mar,
    required double tilt,
    required double modelProbability,
    required double modelThreshold,
  }) {
    // dt giới hạn 1 giây: app bị treo / quay clip xong không cộng dồn bất thường.
    final dt = _lastAt == null
        ? 0.0
        : min(now.difference(_lastAt!).inMilliseconds / 1000.0, 1.0);
    _lastAt = now;

    final events = <FatigueEvent>[];
    var immediate = false;

    // ── Mắt ────────────────────────────────────────────────────────────
    final closed = ear < config.earClosed;
    if (closed) {
      _closedSince ??= now;
      _lastOpenSince = null;
      final closedFor = now.difference(_closedSince!);
      if (!_immediateFired && closedFor >= config.immediateAlarmClosure) {
        _immediateFired = true;
        immediate = true;
      }
    } else {
      _lastOpenSince ??= now;
      if (_closedSince != null) {
        final closedFor = now.difference(_closedSince!);
        if (closedFor >= config.microsleepMin) {
          events.add(
            FatigueEvent(
              FatigueEventKind.microsleep,
              config.microsleepPoints,
              closedFor,
            ),
          );
        } else if (closedFor >= config.longClosureMin) {
          events.add(
            FatigueEvent(
              FatigueEventKind.longClosure,
              config.longClosurePoints,
              closedFor,
            ),
          );
        }
        // Ngắn hơn longClosureMin (gồm chớp mắt <= blinkMax): bỏ qua.
        _closedSince = null;
        _immediateFired = false;
      }
    }

    // ── Ngáp ───────────────────────────────────────────────────────────
    if (mar >= config.yawnMar) {
      _yawnSince ??= now;
    } else if (_yawnSince != null) {
      final yawnFor = now.difference(_yawnSince!);
      if (yawnFor >= config.yawnMin) {
        events.add(
          FatigueEvent(FatigueEventKind.yawn, config.yawnPoints, yawnFor),
        );
      }
      _yawnSince = null;
    }

    // ── Gục / nghiêng đầu (so với tư thế quen, học dần lúc tỉnh táo) ────
    final baseline = _tiltBaseline;
    if (baseline == null) {
      _tiltBaseline = tilt;
    } else if ((tilt - baseline).abs() >= config.headDropDegrees) {
      _tiltSince ??= now;
      final tiltFor = now.difference(_tiltSince!);
      if (!_tiltCounted && tiltFor >= config.headDropMin) {
        _tiltCounted = true;
        events.add(
          FatigueEvent(
            FatigueEventKind.headDrop,
            config.headDropPoints,
            tiltFor,
          ),
        );
      }
    } else {
      _tiltSince = null;
      _tiltCounted = false;
      if (!closed) _tiltBaseline = baseline * 0.98 + tilt * 0.02;
    }

    // ── Model: cộng theo từng giây đủ, không theo từng khung ───────────
    final modelSaysDrowsy = modelProbability >= modelThreshold;
    if (modelSaysDrowsy) {
      _modelSeconds += dt;
      while (_modelSeconds >= 1.0) {
        _modelSeconds -= 1.0;
        events.add(
          FatigueEvent(
            FatigueEventKind.modelDrowsy,
            config.modelPointsPerSecond,
            const Duration(seconds: 1),
          ),
        );
      }
    } else {
      _modelSeconds = 0;
    }

    // ── Cộng / giảm điểm ───────────────────────────────────────────────
    for (final e in events) {
      _score += e.points;
      _counts.update(e.kind, (c) => c + 1, ifAbsent: () => 1);
    }
    final alert = !closed && !modelSaysDrowsy && _yawnSince == null;
    if (events.isEmpty && alert) _score -= config.decayPerSecond * dt;
    _score = _score.clamp(0, config.maxScore).toDouble();

    final previous = _level;
    _level = immediate ? FatigueLevel.alarm : _levelFor(_score);
    // Đang báo động thì giữ mức báo động tới khi acknowledgeAlarm().
    if (previous == FatigueLevel.alarm && _level != FatigueLevel.alarm) {
      _level = FatigueLevel.alarm;
    }

    return FatigueUpdate(
      score: _score,
      level: _level,
      events: events
          .where((e) => e.kind != FatigueEventKind.modelDrowsy)
          .toList(),
      enteredReminder:
          previous == FatigueLevel.normal && _level == FatigueLevel.reminder,
      enteredAlarm:
          previous != FatigueLevel.alarm && _level == FatigueLevel.alarm,
      immediate: immediate,
    );
  }

  FatigueLevel _levelFor(double s) {
    if (s >= config.alarmScore) return FatigueLevel.alarm;
    if (s >= config.reminderScore) return FatigueLevel.reminder;
    return FatigueLevel.normal;
  }
}
