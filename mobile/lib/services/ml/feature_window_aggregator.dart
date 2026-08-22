import 'dart:math';

import 'baseline_calibrator.dart';
import 'landmark_feature_service.dart';

/// Tái hiện đúng BUOC 4 của Notebook 2 (aggregate_window) — cửa sổ trượt
/// [windowSize] mẫu, bước [stepSize] mẫu. Ở đây EAR_z/MAR_z dùng
/// [EarMarBaseline] hiệu chỉnh đầu phiên thay vì "Alert-only baseline theo
/// nhãn" (không thể tái tạo lúc chạy thật — xem baseline_calibrator.dart).
///
/// LƯU Ý ddof (rất dễ làm sai): code train dùng `numpy_array.std()` cho
/// EAR/MAR/EAR_z/MAR_z/TILT (ddof=0, chia N) nhưng dùng
/// `pandas_series.std()` riêng cho EAR_vel (ddof=1, chia N-1) — 2 công thức
/// std KHÁC NHAU trong cùng 1 hàm gốc. Đây có vẻ là chỗ không nhất quán
/// trong code train, nhưng model đã học trên đúng cách tính đó nên phải
/// giữ nguyên, không "sửa cho nhất quán".
class FeatureWindowAggregator {
  FeatureWindowAggregator({
    this.windowSize = 60,
    this.stepSize = 15,
    this.earBlinkThreshold = -1.0,
    this.marYawnThreshold = 0.6,
  });

  final int windowSize;
  final int stepSize;
  final double earBlinkThreshold;
  final double marYawnThreshold;

  final List<RawFrameSignal> _window = [];
  int _samplesSinceLastEmit = 0;

  /// Trả về map tên-feature -> giá trị khi đủ 1 cửa sổ mới (mỗi [stepSize]
  /// mẫu, sau khi đã tích đủ [windowSize] mẫu đầu tiên); null nếu chưa tới
  /// lúc emit.
  Map<String, double>? addSample(RawFrameSignal signal, EarMarBaseline baseline) {
    _window.add(signal);
    if (_window.length > windowSize) _window.removeAt(0);
    _samplesSinceLastEmit++;

    final windowFull = _window.length == windowSize;
    if (!windowFull || _samplesSinceLastEmit < stepSize) return null;

    _samplesSinceLastEmit = 0;
    return _aggregate(_window, baseline);
  }

  Map<String, double> _aggregate(List<RawFrameSignal> w, EarMarBaseline baseline) {
    final ear = w.map((s) => s.ear).toList();
    final mar = w.map((s) => s.mar).toList();
    final tilt = w.map((s) => s.tilt).toList();
    final earVel = w.map((s) => s.earVel).toList();
    final marVel = w.map((s) => s.marVel).toList();
    final earZ = ear.map(baseline.earZ).toList();
    final marZ = mar.map(baseline.marZ).toList();

    final earMean = _mean(ear);
    final marMean = _mean(mar);

    final isClosed = earZ.map((z) => z < earBlinkThreshold).toList();
    final isYawning = mar.map((m) => m > marYawnThreshold).toList();

    return {
      'EAR_mean': earMean,
      'EAR_std': _populationStd(ear),
      'EAR_min': ear.reduce(min),
      'EAR_max': ear.reduce(max),
      'EAR_range': ear.reduce(max) - ear.reduce(min),
      'MAR_mean': marMean,
      'MAR_std': _populationStd(mar),
      'MAR_min': mar.reduce(min),
      'MAR_max': mar.reduce(max),
      'MAR_range': mar.reduce(max) - mar.reduce(min),
      'EAR_z_mean': _mean(earZ),
      'EAR_z_std': _populationStd(earZ),
      'EAR_z_min': earZ.reduce(min),
      'EAR_z_max': earZ.reduce(max),
      'EAR_z_range': earZ.reduce(max) - earZ.reduce(min),
      'MAR_z_mean': _mean(marZ),
      'MAR_z_std': _populationStd(marZ),
      'TILT_mean': _mean(tilt),
      'TILT_std': _populationStd(tilt),
      'PERCLOS': isClosed.where((c) => c).length / w.length,
      'EAR_slope': _linearSlope(ear),
      'blink_rate': _countRisingEdges(isClosed).toDouble(),
      'yawn_count': _countRisingEdges(isYawning).toDouble(),
      'EAR_vel_mean': _mean(earVel),
      'EAR_vel_std': _sampleStd(earVel),
      'MAR_vel_mean': _mean(marVel),
      'avg_blink_duration': _avgRunLength(isClosed),
      'EAR_MAR_ratio': earMean / (marMean + 1e-6),
    };
  }

  double _mean(List<double> xs) => xs.reduce((a, b) => a + b) / xs.length;

  double _populationStd(List<double> xs) {
    final m = _mean(xs);
    final variance = xs.map((x) => (x - m) * (x - m)).reduce((a, b) => a + b) / xs.length;
    return sqrt(variance);
  }

  double _sampleStd(List<double> xs) {
    if (xs.length < 2) return 0.0;
    final m = _mean(xs);
    final variance = xs.map((x) => (x - m) * (x - m)).reduce((a, b) => a + b) / (xs.length - 1);
    return sqrt(variance);
  }

  double _linearSlope(List<double> arr) {
    final n = arr.length;
    if (n < 2) return 0.0;
    final t = List<double>.generate(n, (i) => i.toDouble());
    final tMean = _mean(t);
    final xMean = _mean(arr);
    var num = 0.0;
    var den = 0.0;
    for (var i = 0; i < n; i++) {
      num += (t[i] - tMean) * (arr[i] - xMean);
      den += (t[i] - tMean) * (t[i] - tMean);
    }
    return den == 0 ? 0.0 : num / den;
  }

  int _countRisingEdges(List<bool> xs) {
    var count = 0;
    var prev = false;
    for (final cur in xs) {
      if (cur && !prev) count++;
      prev = cur;
    }
    return count;
  }

  double _avgRunLength(List<bool> xs) {
    final runs = <int>[];
    var count = 0;
    for (final c in xs) {
      if (c) {
        count++;
      } else {
        if (count > 0) runs.add(count);
        count = 0;
      }
    }
    if (count > 0) runs.add(count);
    if (runs.isEmpty) return 0.0;
    return runs.reduce((a, b) => a + b) / runs.length;
  }
}
