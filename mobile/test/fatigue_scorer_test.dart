import 'package:flutter_test/flutter_test.dart';
import 'package:apphotrotaixe/services/ml/fatigue_scorer.dart';

/// Giả lập camera ~6 khung/giây: mắt mở EAR 0.30, nhắm 0.15.
class _Sim {
  _Sim([FatigueConfig? config]) : scorer = FatigueScorer(config);

  final FatigueScorer scorer;
  DateTime t = DateTime(2026, 10, 6, 2, 0);
  static const frame = Duration(milliseconds: 166);
  final updates = <FatigueUpdate>[];

  FatigueUpdate _step({
    double ear = 0.30,
    double mar = 0.2,
    double tilt = 0,
    double prob = 0.1,
  }) {
    t = t.add(frame);
    final u = scorer.update(
      now: t,
      ear: ear,
      mar: mar,
      tilt: tilt,
      modelProbability: prob,
      modelThreshold: 0.5,
    );
    updates.add(u);
    return u;
  }

  void open(Duration d, {double prob = 0.1}) {
    for (var e = Duration.zero; e < d; e += frame) {
      _step(prob: prob);
    }
  }

  void closed(Duration d) {
    for (var e = Duration.zero; e < d; e += frame) {
      _step(ear: 0.15);
    }
  }

  void yawn(Duration d) {
    for (var e = Duration.zero; e < d; e += frame) {
      _step(mar: 0.8);
    }
  }

  bool get anyAlarm => updates.any((u) => u.enteredAlarm);
  bool get anyReminder => updates.any((u) => u.enteredReminder);
}

void main() {
  test('chớp mắt bình thường không cộng điểm', () {
    final sim = _Sim()..open(const Duration(seconds: 1));
    for (var i = 0; i < 40; i++) {
      sim
        ..closed(const Duration(milliseconds: 300))
        ..open(const Duration(seconds: 3));
    }
    expect(sim.scorer.score, 0);
    expect(sim.scorer.level, FatigueLevel.normal);
    expect(sim.anyReminder, isFalse);
    expect(sim.anyAlarm, isFalse);
  });

  test('một lần nhắm mắt lâu chỉ cộng điểm, không báo động', () {
    final sim = _Sim()
      ..open(const Duration(seconds: 1))
      ..closed(const Duration(milliseconds: 900))
      ..open(const Duration(milliseconds: 500));
    expect(sim.scorer.score, closeTo(10, 0.5));
    expect(sim.anyAlarm, isFalse);
  });

  test('nhắm mắt lâu lặp lại -> nhắc nhẹ rồi báo động', () {
    final sim = _Sim()..open(const Duration(seconds: 1));
    // Mỗi lần +10, xen giữa 2 giây tỉnh táo điểm giảm ~0,4 -> cần 4 lần.
    for (var i = 0; i < 4; i++) {
      sim
        ..closed(const Duration(milliseconds: 900))
        ..open(const Duration(seconds: 2));
    }
    expect(sim.anyReminder, isTrue, reason: '4 lần ~38 điểm');
    expect(sim.anyAlarm, isFalse);
    for (var i = 0; i < 3; i++) {
      sim
        ..closed(const Duration(milliseconds: 900))
        ..open(const Duration(seconds: 2));
    }
    expect(sim.anyAlarm, isTrue, reason: '7 lần ~66 điểm');
    expect(sim.updates.firstWhere((u) => u.enteredAlarm).immediate, isFalse);
  });

  test('nhắm mắt liên tục quá 2 giây -> báo động ngay dù điểm thấp', () {
    final sim = _Sim()
      ..open(const Duration(seconds: 1))
      ..closed(const Duration(milliseconds: 2300));
    final alarm = sim.updates.firstWhere((u) => u.enteredAlarm);
    expect(alarm.immediate, isTrue);
    expect(alarm.score, lessThan(60));
  });

  test('tỉnh táo thì điểm tự giảm về 0', () {
    final sim = _Sim()..open(const Duration(seconds: 1));
    for (var i = 0; i < 3; i++) {
      sim
        ..closed(const Duration(milliseconds: 900))
        ..open(const Duration(seconds: 1));
    }
    expect(sim.scorer.score, greaterThan(25));
    sim.open(const Duration(minutes: 3));
    expect(sim.scorer.score, 0);
    expect(sim.scorer.level, FatigueLevel.normal);
  });

  test('model báo buồn ngủ liên tục 30 giây -> báo động', () {
    final sim = _Sim()..open(const Duration(seconds: 31), prob: 0.9);
    expect(sim.anyAlarm, isTrue);
  });

  test('ngáp được tính, cộng điểm ít', () {
    final sim = _Sim()
      ..open(const Duration(seconds: 1))
      ..yawn(const Duration(milliseconds: 1500))
      ..open(const Duration(milliseconds: 300));
    expect(sim.scorer.score, closeTo(5, 0.5));
    expect(sim.scorer.summary(), contains('ngáp'));
  });

  test('sau khi báo động, điểm hạ về mức nhắc nhẹ và xoá tóm tắt', () {
    final sim = _Sim()..open(const Duration(seconds: 31), prob: 0.9);
    expect(sim.scorer.summary(), isNotEmpty);
    sim.scorer.acknowledgeAlarm();
    expect(sim.scorer.score, 30);
    expect(sim.scorer.summary(), isEmpty);
  });

  test('đọc tham số từ model_meta.json', () {
    final c = FatigueConfig.fromJson({
      'alarm_score': 80,
      'immediate_alarm_closure_ms': 2500,
    }, earClosed: 0.2);
    expect(c.alarmScore, 80);
    expect(c.immediateAlarmClosure, const Duration(milliseconds: 2500));
    expect(c.earClosed, 0.2);
    expect(c.reminderScore, 30);
  });
}
