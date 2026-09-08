import 'dart:collection';
import 'dart:math';

import 'landmark_feature_service.dart';

/// Tính 11 đặc trưng cho model **MLP-Feature** — mỗi khung hình đã lấy mẫu
/// cho ra 1 vector (khác model SVM cũ: không còn cửa sổ trượt 60/15, không
/// còn baseline cá nhân / EAR_z).
///
/// Khớp CHÍNH XÁC `compute_temporal_features()` trong notebook
/// tcg-paper.ipynb (CELL 4):
///   - ROLLING_WINDOW  = 5   (ear/mar/tilt roll mean & std)
///   - PERCLOS_WINDOW  = 30  (perclos_true, blink_rate)
///   - EAR_BLINK_THRESH = 0.21  (ngưỡng cố định, mắt "nhắm" khi ear < 0.21)
///
/// LƯU Ý:
///   * `*_roll_std` dùng std MẪU (ddof=1) — đúng như `pandas.Series.std()`.
///     Khi cửa sổ chỉ có 1 mẫu, pandas trả NaN -> `.fillna(0)` -> ở đây 0.0.
///   * `blink_rate` đếm sự kiện mắt **MỞ RA** (closed 1 -> 0) trong 30 khung,
///     không phải số lần nhắm. Drowsy > Alert (theo notebook).
///   * `mar_diff` = mar[t] - mar[t-1], khung đầu = 0.
class FeatureWindowAggregator {
  FeatureWindowAggregator({
    this.rollingWindow = 5,
    this.perclosWindow = 30,
    this.earBlinkThreshold = 0.21,
  });

  final int rollingWindow;
  final int perclosWindow;
  final double earBlinkThreshold;

  final ListQueue<double> _ear = ListQueue();
  final ListQueue<double> _mar = ListQueue();
  final ListQueue<double> _tilt = ListQueue();
  final ListQueue<double> _closed = ListQueue(); // 0/1, tối đa perclosWindow
  final ListQueue<double> _opening = ListQueue(); // 0/1, tối đa perclosWindow

  double? _prevMar;
  double? _prevClosed;

  /// Xoá toàn bộ lịch sử — gọi khi bắt đầu phiên mới hoặc sau khi mất khuôn
  /// mặt quá lâu (gap reset).
  void reset() {
    _ear.clear();
    _mar.clear();
    _tilt.clear();
    _closed.clear();
    _opening.clear();
    _prevMar = null;
    _prevClosed = null;
  }

  /// Trả về map 11 đặc trưng cho khung hiện tại. LUÔN trả về giá trị (khác
  /// bản cũ trả null tới khi đủ cửa sổ) vì model mới dự đoán theo từng khung.
  Map<String, double> addSample(RawFrameSignal s) {
    final ear = s.ear;
    final mar = s.mar;
    final tilt = s.tilt;

    _push(_ear, ear, rollingWindow);
    _push(_mar, mar, rollingWindow);
    _push(_tilt, tilt, rollingWindow);

    final marDiff = _prevMar == null ? 0.0 : mar - _prevMar!;
    _prevMar = mar;

    final closed = ear < earBlinkThreshold ? 1.0 : 0.0;
    final opening = (_prevClosed == 1.0 && closed == 0.0) ? 1.0 : 0.0;
    _prevClosed = closed;
    _push(_closed, closed, perclosWindow);
    _push(_opening, opening, perclosWindow);

    final earRollMean = _mean(_ear);
    final marRollMean = _mean(_mar);

    return {
      'ear': ear,
      'mar': mar,
      'ear_roll_mean': earRollMean,
      'ear_roll_std': _sampleStd(_ear),
      'mar_roll_mean': marRollMean,
      'mar_roll_std': _sampleStd(_mar),
      'mar_diff': marDiff,
      'ear_mar_ratio_roll': earRollMean / (marRollMean + 1e-6),
      'perclos_true': _mean(_closed),
      'blink_rate': _sum(_opening),
      'head_tilt_roll_std': _sampleStd(_tilt),
    };
  }

  void _push(ListQueue<double> q, double v, int maxLen) {
    q.addLast(v);
    if (q.length > maxLen) q.removeFirst();
  }

  double _mean(Iterable<double> xs) {
    var sum = 0.0;
    var n = 0;
    for (final x in xs) {
      sum += x;
      n++;
    }
    return n == 0 ? 0.0 : sum / n;
  }

  double _sum(Iterable<double> xs) => xs.fold(0.0, (a, b) => a + b);

  /// std mẫu (ddof=1). < 2 phần tử -> 0.0 (khớp pandas NaN -> fillna(0)).
  double _sampleStd(Iterable<double> xsIter) {
    final xs = xsIter.toList(growable: false);
    if (xs.length < 2) return 0.0;
    final m = _mean(xs);
    var acc = 0.0;
    for (final x in xs) {
      acc += (x - m) * (x - m);
    }
    return sqrt(acc / (xs.length - 1));
  }
}
