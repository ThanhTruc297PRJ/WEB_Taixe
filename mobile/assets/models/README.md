# assets/models/

| File | Dùng để làm gì | Bundle vào app? |
|---|---|---|
| `drowsiness_model.tflite` | Model buồn ngủ thật, chạy trong app qua `TFLiteModelService` | ✅ (khai báo trong `pubspec.yaml`) |
| `model_meta.json` | threshold, window_size, step_size, thứ tự 28 feature | ✅ |
| `best_model_svm_window.pkl` | Model gốc (scikit-learn) — nguồn để convert lại nếu retrain | ❌ chỉ để tham khảo/tái tạo |
| `model_meta.pkl` | Bản gốc Python của `model_meta.json` | ❌ chỉ để tham khảo |

## Nếu model được train lại

1. Ghi đè `best_model_svm_window.pkl` + `model_meta.pkl` bằng bản mới.
2. Chạy `python scripts/convert_svm_to_tflite.py` (xem file đó để biết vì
   sao phải tự dựng lại công thức toán thay vì dùng skl2onnx/onnx2tf thẳng —
   TFLite output của 2 công cụ đó dùng custom op mà `tflite_flutter` không
   chạy được).
3. Nếu `feature_cols`/`window_size`/`step_size`/`threshold` trong
   `model_meta.pkl` thay đổi, chạy lại đoạn export JSON ở
   `docs/MODEL_CONVERSION.md` để cập nhật `model_meta.json`.
4. `flutter pub get` để Flutter re-scan asset.
