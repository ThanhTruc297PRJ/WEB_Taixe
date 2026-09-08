import 'dart:convert';

import 'package:flutter/services.dart' show rootBundle;
import 'package:tflite_flutter/tflite_flutter.dart';

/// Metadata đi kèm model (assets/models/model_meta.json — sinh bởi
/// scripts/convert_mlp_to_tflite.py).
class DrowsinessModelMeta {
  const DrowsinessModelMeta({
    required this.threshold,
    required this.rollingWindow,
    required this.perclosWindow,
    required this.earBlinkThreshold,
    required this.emaBeta,
    required this.emaGapReset,
    required this.featureCols,
  });

  /// Ngưỡng quyết định trên xác suất (đã EMA): >= threshold -> buồn ngủ.
  final double threshold;

  /// Cửa sổ tính *_roll_mean/std (khung hình).
  final int rollingWindow;

  /// Cửa sổ tính perclos_true / blink_rate (khung hình).
  final int perclosWindow;

  /// Ngưỡng EAR để coi mắt là "nhắm".
  final double earBlinkThreshold;

  /// Hệ số làm mượt EMA cho xác suất đầu ra: s = beta*s + (1-beta)*p.
  final double emaBeta;

  /// Mất khuôn mặt quá số khung này thì reset EMA + lịch sử đặc trưng.
  final int emaGapReset;

  final List<String> featureCols;

  factory DrowsinessModelMeta.fromJson(Map<String, dynamic> json) =>
      DrowsinessModelMeta(
        threshold: (json['threshold'] as num).toDouble(),
        rollingWindow: (json['rolling_window'] as num).toInt(),
        perclosWindow: (json['perclos_window'] as num).toInt(),
        earBlinkThreshold: (json['ear_blink_thresh'] as num).toDouble(),
        emaBeta: (json['ema_beta'] as num).toDouble(),
        emaGapReset: (json['ema_gap_reset'] as num).toInt(),
        featureCols: List<String>.from(json['feature_cols'] as List),
      );
}

/// Model buồn ngủ **MLP-Feature**: pipeline StandardScaler + MLP (128-64-32,
/// relu, sigmoid) train bằng scikit-learn, convert sang .tflite bằng
/// scripts/convert_mlp_to_tflite.py (đã verify khớp predict_proba gốc, sai
/// lệch ~1e-7).
///
/// Input: 11 giá trị ĐÚNG THỨ TỰ theo [meta.featureCols] (xem
/// FeatureWindowAggregator). Output: xác suất buồn ngủ [0, 1] cho 1 khung —
/// MonitoringViewModel làm mượt bằng EMA rồi mới so [meta.threshold].
class TFLiteModelService {
  Interpreter? _interpreter;
  DrowsinessModelMeta? _meta;

  bool get isLoaded => _interpreter != null;
  DrowsinessModelMeta? get meta => _meta;

  Future<bool> load({
    String modelAsset = 'assets/models/drowsiness_model.tflite',
    String metaAsset = 'assets/models/model_meta.json',
  }) async {
    try {
      final metaJson = jsonDecode(await rootBundle.loadString(metaAsset));
      _meta = DrowsinessModelMeta.fromJson(metaJson as Map<String, dynamic>);
      _interpreter = await Interpreter.fromAsset(modelAsset);
      return true;
    } catch (_) {
      _interpreter = null;
      _meta = null;
      return false;
    }
  }

  /// [namedFeatures] phải chứa đúng các key trong [meta.featureCols] (thứ tự
  /// trong map không quan trọng — tự sắp xếp lại theo đúng thứ tự model cần
  /// trước khi chạy, tránh lỗi đảo cột thủ công).
  /// Trả về xác suất buồn ngủ trong [0, 1]; so với [meta.threshold] để ra
  /// quyết định cảnh báo.
  double predictDrowsyProbability(Map<String, double> namedFeatures) {
    final interpreter = _interpreter;
    final meta = _meta;
    if (interpreter == null || meta == null) {
      throw StateError('Model chưa được nạp — gọi load() trước.');
    }

    final ordered = <double>[];
    for (final name in meta.featureCols) {
      final value = namedFeatures[name];
      if (value == null) {
        throw ArgumentError('Thiếu feature "$name" trong namedFeatures.');
      }
      ordered.add(value);
    }

    final input = [ordered];
    final output = List.filled(1, 0.0).reshape([1]);
    interpreter.run(input, output);
    return (output[0] as double);
  }

  void dispose() {
    _interpreter?.close();
    _interpreter = null;
    _meta = null;
  }
}
