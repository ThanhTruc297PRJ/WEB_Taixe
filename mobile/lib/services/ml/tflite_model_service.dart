import 'dart:convert';

import 'package:flutter/services.dart' show rootBundle;
import 'package:tflite_flutter/tflite_flutter.dart';

/// Metadata đi kèm model (assets/models/model_meta.json — export từ
/// model_meta.pkl vì Dart không đọc được pickle của Python).
class DrowsinessModelMeta {
  const DrowsinessModelMeta({
    required this.threshold,
    required this.windowSize,
    required this.stepSize,
    required this.featureCols,
  });

  final double threshold;
  final int windowSize;
  final int stepSize;
  final List<String> featureCols;

  factory DrowsinessModelMeta.fromJson(Map<String, dynamic> json) => DrowsinessModelMeta(
        threshold: (json['threshold'] as num).toDouble(),
        windowSize: json['window_size'] as int,
        stepSize: json['step_size'] as int,
        featureCols: List<String>.from(json['feature_cols'] as List),
      );
}

/// Model buồn ngủ thật (TASK-A02/SUB-01): pipeline RobustScaler + SVM (RBF,
/// calibrated) đã train bằng scikit-learn, convert sang .tflite bằng
/// scripts/convert_svm_to_tflite.py (xem file đó để hiểu vì sao KHÔNG convert
/// thẳng qua skl2onnx/onnx2tf — model đó không load được bằng runtime chuẩn).
///
/// Input: đúng [meta.featureCols.length] giá trị, ĐÚNG THỨ TỰ theo
/// [meta.featureCols] (28 đặc trưng EAR/MAR/PERCLOS/... tính theo cửa sổ
/// [meta.windowSize] khung hình). Việc tính ra các đặc trưng này từ
/// camera/landmark CHƯA được implement — xem MonitoringViewModel.
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
