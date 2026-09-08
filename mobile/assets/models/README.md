# assets/models/

| File | Dùng để làm gì | Bundle vào app? |
|---|---|---|
| `drowsiness_model.tflite` | Model buồn ngủ **MLP-Feature** đang chạy — StandardScaler + MLP(128-64-32), input 11 đặc trưng | ✅ (khai báo trong `pubspec.yaml`) |
| `model_meta.json` | threshold, rolling_window, perclos_window, ear_blink_thresh, ema_beta, thứ tự 11 feature | ✅ |
| `mlp_feature_result.pkl` | Model gốc (scikit-learn Pipeline) — nguồn để convert lại nếu retrain | ❌ chỉ để tham khảo/tái tạo |
| `drowsiness_svm_legacy.tflite` | Model SVM cũ (28 feature) — giữ lại phòng cần đối chiếu | ❌ |
| `best_model_svm_window.pkl`, `model_meta.pkl` | Bản gốc của model SVM cũ | ❌ |

## Nếu train lại model MLP

1. Ghi đè `mlp_feature_result.pkl` bằng bản mới (dict có key `model` là
   sklearn Pipeline, `feature_cols` là danh sách 11 tên feature).
2. Chạy `python scripts/convert_mlp_to_tflite.py` — sinh
   `drowsiness_mlp.tflite` + `model_meta_mlp.json`, verify khớp
   `predict_proba` gốc (sai lệch phải < 1e-4).
3. Đổi tên 2 file đó thành `drowsiness_model.tflite` / `model_meta.json`.
4. Nếu `ROLLING_WINDOW` / `PERCLOS_WINDOW` / `EAR_BLINK_THRESH` / `EMA_BETA`
   trong notebook đổi, sửa hằng số tương ứng ở đầu
   `scripts/convert_mlp_to_tflite.py` rồi convert lại.
5. `flutter pub get` để Flutter re-scan assets.

## Nếu đổi bộ đặc trưng (số lượng / công thức)

Phải sửa `lib/services/ml/feature_window_aggregator.dart` cho khớp
`compute_temporal_features()` trong notebook — đây là chỗ dễ sai nhất, phải
verify range giá trị trên thiết bị thật.
