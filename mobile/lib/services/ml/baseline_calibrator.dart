import 'dart:math';

import 'landmark_feature_service.dart';

/// Baseline cá nhân cho EAR/MAR — thay thế "Alert-only baseline theo nhãn"
/// dùng lúc train (không khả thi lúc chạy thật vì không có nhãn). Thay vào
/// đó: giả định vài giây đầu mỗi phiên giám sát là tài xế đang tỉnh táo, và
/// dùng mean/std của EAR/MAR trong khoảng đó làm baseline cho suốt phiên.
class EarMarBaseline {
  const EarMarBaseline({
    required this.earMean,
    required this.earStd,
    required this.marMean,
    required this.marStd,
  });

  final double earMean;
  final double earStd;
  final double marMean;
  final double marStd;

  double earZ(double ear) => earStd < 1e-6 ? 0.0 : (ear - earMean) / earStd;
  double marZ(double mar) => marStd < 1e-6 ? 0.0 : (mar - marMean) / marStd;
}

/// Thu thập mẫu trong giai đoạn hiệu chỉnh đầu phiên rồi chốt baseline.
/// [minSamples] mặc định 30 mẫu ~ 5 giây ở nhịp lấy mẫu ~6Hz.
class BaselineCalibrator {
  BaselineCalibrator({this.minSamples = 30});

  final int minSamples;
  final List<double> _ears = [];
  final List<double> _mars = [];

  bool get isReady => _ears.length >= minSamples;
  int get collected => _ears.length;

  void addSample(RawFrameSignal signal) {
    _ears.add(signal.ear);
    _mars.add(signal.mar);
  }

  EarMarBaseline finish() {
    if (!isReady) {
      throw StateError('Chưa đủ mẫu hiệu chỉnh ($collected/$minSamples).');
    }
    return EarMarBaseline(
      earMean: _mean(_ears),
      earStd: _populationStd(_ears),
      marMean: _mean(_mars),
      marStd: _populationStd(_mars),
    );
  }

  void reset() {
    _ears.clear();
    _mars.clear();
  }

  double _mean(List<double> xs) => xs.reduce((a, b) => a + b) / xs.length;

  double _populationStd(List<double> xs) {
    final m = _mean(xs);
    final variance = xs.map((x) => (x - m) * (x - m)).reduce((a, b) => a + b) / xs.length;
    return sqrt(variance);
  }
}
