import 'package:flutter_test/flutter_test.dart';

import 'package:apphotrotaixe/data/models/event_log.dart';
import 'package:apphotrotaixe/services/ml/feature_window_aggregator.dart';
import 'package:apphotrotaixe/services/ml/landmark_feature_service.dart';

// Không test MonitoringScreen/DriverSafetyApp/LandmarkFeatureService trực
// tiếp ở đây: chúng phụ thuộc camera/sqflite/ML Kit/flutter_foreground_task
// qua platform channel, vốn không có sẵn trong môi trường `flutter test`
// thuần Dart. Test phần logic thuần Dart (tính toán feature) — đây cũng là
// phần dễ sai nhất vì phải khớp chính xác công thức lúc train.
void main() {
  group('EventLog', () {
    test('toMap/fromMap round-trip giữ nguyên dữ liệu', () {
      final log = EventLog(
        type: EventType.drowsiness,
        message: 'Phát hiện mắt nhắm kéo dài',
        timestamp: DateTime.fromMillisecondsSinceEpoch(1700000000000),
        confidence: 0.12,
      );

      final restored = EventLog.fromMap(log.toMap());

      expect(restored.type, EventType.drowsiness);
      expect(restored.message, log.message);
      expect(restored.timestamp, log.timestamp);
      expect(restored.confidence, 0.12);
      expect(restored.synced, isFalse);
    });
  });

  group('FeatureWindowAggregator (MLP-Feature, 11 đặc trưng)', () {
    RawFrameSignal sig(double ear, double mar, double tilt) =>
        RawFrameSignal(ear: ear, mar: mar, tilt: tilt, earVel: 0, marVel: 0);

    test('khung đầu tiên: roll_std = 0 (pandas NaN -> fillna 0)', () {
      final agg = FeatureWindowAggregator();
      final f = agg.addSample(sig(0.30, 0.40, 2.0));

      expect(f['ear'], 0.30);
      expect(f['mar'], 0.40);
      expect(f['ear_roll_mean'], closeTo(0.30, 1e-12));
      expect(f['ear_roll_std'], 0.0);
      expect(f['mar_roll_std'], 0.0);
      expect(f['head_tilt_roll_std'], 0.0);
      expect(f['mar_diff'], 0.0); // không có khung trước
      expect(f['perclos_true'], 0.0); // ear 0.30 >= 0.21 -> mắt mở
      expect(f['blink_rate'], 0.0);
    });

    test('công thức 11 đặc trưng khớp tính tay sau 5 khung', () {
      final agg = FeatureWindowAggregator();
      // ear: [.30, .28, .15, .15, .30]  (.15 < 0.21 -> mắt nhắm ở khung 3,4)
      // mar: [.40, .42, .50, .55, .45]
      // tilt:[2.0, 2.0, 3.0, 3.0, 2.0]
      final frames = [
        sig(0.30, 0.40, 2.0),
        sig(0.28, 0.42, 2.0),
        sig(0.15, 0.50, 3.0),
        sig(0.15, 0.55, 3.0),
        sig(0.30, 0.45, 2.0),
      ];
      Map<String, double>? f;
      for (final s in frames) {
        f = agg.addSample(s);
      }
      f = f!;

      expect(f['ear'], 0.30);
      expect(f['mar'], 0.45);
      expect(f['ear_roll_mean'], closeTo(0.236, 1e-9));
      expect(f['ear_roll_std'], closeTo(0.07893034904268446, 1e-12));
      expect(f['mar_roll_mean'], closeTo(0.464, 1e-9));
      expect(f['mar_roll_std'], closeTo(0.061073725938409894, 1e-12));
      expect(f['mar_diff'], closeTo(-0.10, 1e-9)); // 0.45 - 0.55
      expect(f['ear_mar_ratio_roll'], closeTo(0.5086195934922555, 1e-12));
      expect(f['perclos_true'], closeTo(0.4, 1e-12)); // 2/5 khung nhắm
      expect(f['blink_rate'], closeTo(1.0, 1e-12)); // 1 lần mắt mở ra (khung 5)
      expect(f['head_tilt_roll_std'], closeTo(0.5477225575051661, 1e-12));
    });

    test('cửa sổ roll chỉ giữ 5 khung gần nhất', () {
      final agg = FeatureWindowAggregator();
      // 4 khung EAR cao rồi 5 khung EAR = 0.20 -> roll_mean phải = 0.20
      for (final e in [0.35, 0.35, 0.35, 0.35]) {
        agg.addSample(sig(e, 0.40, 0.0));
      }
      Map<String, double>? f;
      for (var i = 0; i < 5; i++) {
        f = agg.addSample(sig(0.20, 0.40, 0.0));
      }
      expect(f!['ear_roll_mean'], closeTo(0.20, 1e-12));
      expect(f['ear_roll_std'], closeTo(0.0, 1e-12));
    });

    test('reset xoá sạch lịch sử', () {
      final agg = FeatureWindowAggregator();
      agg.addSample(sig(0.15, 0.60, 1.0)); // mắt nhắm
      agg.reset();
      final f = agg.addSample(sig(0.30, 0.40, 2.0));
      expect(f['perclos_true'], 0.0);
      expect(f['mar_diff'], 0.0);
      expect(f['ear_roll_mean'], closeTo(0.30, 1e-12));
    });
  });
}
