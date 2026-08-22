import 'package:flutter_test/flutter_test.dart';

import 'package:apphotrotaixe/data/models/event_log.dart';
import 'package:apphotrotaixe/services/ml/baseline_calibrator.dart';
import 'package:apphotrotaixe/services/ml/feature_window_aggregator.dart';
import 'package:apphotrotaixe/services/ml/landmark_feature_service.dart';

// Không test MonitoringScreen/DriverSafetyApp/LandmarkFeatureService trực
// tiếp ở đây: chúng phụ thuộc camera/sqflite/ML Kit/flutter_foreground_task
// qua platform channel, vốn không có sẵn trong môi trường `flutter test`
// thuần Dart. Test phần logic thuần Dart (tính toán feature/baseline) —
// đây cũng là phần dễ sai nhất vì phải khớp chính xác công thức lúc train.
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

  group('BaselineCalibrator', () {
    test('tính đúng mean/std (population, ddof=0) sau khi đủ mẫu', () {
      final calibrator = BaselineCalibrator(minSamples: 4);
      for (final ear in [0.30, 0.10, 0.10, 0.30]) {
        calibrator.addSample(RawFrameSignal(ear: ear, mar: 0.5, tilt: 0, earVel: 0, marVel: 0));
      }

      expect(calibrator.isReady, isTrue);
      final baseline = calibrator.finish();

      expect(baseline.earMean, closeTo(0.2, 1e-9));
      expect(baseline.earStd, closeTo(0.1, 1e-9)); // population std, không phải sample std
      expect(baseline.marMean, closeTo(0.5, 1e-9));
      expect(baseline.marStd, closeTo(0.0, 1e-9));
    });

    test('earZ/marZ trả về 0 nếu std ~ 0 (tránh chia 0)', () {
      const baseline = EarMarBaseline(earMean: 0.2, earStd: 0.0, marMean: 0.5, marStd: 0.0);
      expect(baseline.earZ(0.5), 0.0);
      expect(baseline.marZ(0.9), 0.0);
    });
  });

  group('FeatureWindowAggregator', () {
    // window=4, step=2: cửa sổ đầu emit ngay khi đủ 4 mẫu (samples[0:4]),
    // cửa sổ kế tiếp emit sau 2 mẫu mới (samples[2:6]) — khớp cách NB2 tạo
    // window bằng range(0, n-window+1, step).
    const baseline = EarMarBaseline(earMean: 0.30, earStd: 0.10, marMean: 0.50, marStd: 0.05);

    List<RawFrameSignal> fourSignals() => [
          RawFrameSignal(ear: 0.30, mar: 0.5, tilt: 5, earVel: 0.0, marVel: 0),
          RawFrameSignal(ear: 0.10, mar: 0.5, tilt: 5, earVel: -0.2, marVel: 0),
          RawFrameSignal(ear: 0.10, mar: 0.5, tilt: 5, earVel: 0.0, marVel: 0),
          RawFrameSignal(ear: 0.30, mar: 0.5, tilt: 5, earVel: 0.2, marVel: 0),
        ];

    test('chỉ emit khi đủ window, sau đó emit mỗi step mẫu mới', () {
      final aggregator = FeatureWindowAggregator(windowSize: 4, stepSize: 2);
      final emissions = <Map<String, double>?>[];
      for (final s in [...fourSignals(), ...fourSignals().sublist(0, 2)]) {
        emissions.add(aggregator.addSample(s, baseline));
      }
      // 4 mẫu đầu: null, null, null, <window đầu tiên>
      expect(emissions.sublist(0, 3), everyElement(isNull));
      expect(emissions[3], isNotNull);
      // 2 mẫu tiếp theo: null rồi <window thứ hai>
      expect(emissions[4], isNull);
      expect(emissions[5], isNotNull);
    });

    test('công thức feature khớp tính tay cho 1 cửa sổ đã biết trước', () {
      final aggregator = FeatureWindowAggregator(windowSize: 4, stepSize: 2);
      Map<String, double>? result;
      for (final s in fourSignals()) {
        result = aggregator.addSample(s, baseline);
      }
      expect(result, isNotNull);
      final f = result!;

      // ear = [0.30, 0.10, 0.10, 0.30] -> mean=0.2, std population=0.1
      expect(f['EAR_mean'], closeTo(0.2, 1e-9));
      expect(f['EAR_std'], closeTo(0.1, 1e-9));
      expect(f['EAR_range'], closeTo(0.2, 1e-9));
      expect(f['EAR_slope'], closeTo(0.0, 1e-9)); // đối xứng quanh giữa window

      // earZ = (ear-0.3)/0.1 = [0, -2, -2, 0]; ngưỡng mặc định -1.0
      // -> isClosed = [F, T, T, F] -> PERCLOS=0.5, 1 lần chuyển F->T,
      //    1 chuỗi nhắm dài 2 mẫu.
      expect(f['PERCLOS'], closeTo(0.5, 1e-9));
      expect(f['blink_rate'], closeTo(1.0, 1e-9));
      expect(f['avg_blink_duration'], closeTo(2.0, 1e-9));

      // earVel = [0, -0.2, 0, 0.2] -> mean=0, sample std (ddof=1) = sqrt(0.08/3)
      expect(f['EAR_vel_mean'], closeTo(0.0, 1e-9));
      expect(f['EAR_vel_std'], closeTo(0.16329931618554522, 1e-9));

      // mar hằng số 0.5 -> MAR_std=0; EAR_MAR_ratio = 0.2/0.500001
      expect(f['MAR_std'], closeTo(0.0, 1e-9));
      expect(f['EAR_MAR_ratio'], closeTo(0.2 / 0.500001, 1e-6));
      expect(f['yawn_count'], closeTo(0.0, 1e-9));
    });
  });
}
