# Convert model đã train sang .tflite (TASK-A02/SUB-01)

## Model hiện tại của dự án: scikit-learn (RobustScaler + SVM) — ĐÃ XONG

Model buồn ngủ thật (`best_model_svm_window.pkl`) không phải mạng nơ-ron mà
là 1 pipeline scikit-learn (`RobustScaler` → `SVM` RBF, calibrated 2-fold),
nhận 28 đặc trưng EAR/MAR/PERCLOS/... theo cửa sổ (xem `model_meta.pkl`).

**Không dùng `skl2onnx` + `onnx2tf` như hướng dẫn chung bên dưới** — đã thử,
convert "thành công" nhưng model sinh ra dùng custom op
(`ONNX_SCALER`/`ONNX_SVMCLASSIFIER`) mà TFLite runtime chuẩn (cái
`tflite_flutter` dùng) không chạy được — lỗi
`Encountered unresolved custom op: ONNX_SCALER` khi `allocate_tensors()`.

Cách đã dùng: `scripts/convert_svm_to_tflite.py` tự dựng lại đúng công thức
scaler + SVM decision function + Platt calibration bằng phép toán TFLite
gốc (sub/div/exp/reduce_sum/sigmoid) thay vì để skl2onnx gói gọn thành 1 op
lớn. Đã verify output khớp `predict_proba` gốc (sai lệch ~1e-7). Nếu model
này được train lại, chạy lại script đó — không cần đọc phần dưới.

Phần hướng dẫn chung bên dưới dành cho các model khác (ảnh/CNN) nếu sau này
dự án cần thêm, ví dụ model phát hiện vật thể gây mất tập trung.

---

Chọn nhánh theo framework model gốc đã train.

## TensorFlow / Keras (SavedModel hoặc .h5)

```python
import tensorflow as tf

converter = tf.lite.TFLiteConverter.from_saved_model("saved_model_dir")
# Quantization INT8 (nhẹ nhất, cần representative_dataset để đo range hoạt
# động thật của activation — bỏ qua sẽ dùng FP16 kém tối ưu hơn).
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_dataset_gen  # tự viết
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.int8
converter.inference_output_type = tf.int8

tflite_model = converter.convert()
open("drowsiness_model.tflite", "wb").write(tflite_model)
```

Không cần INT8 (ưu tiên độ chính xác hơn dung lượng) thì bỏ 3 dòng liên
quan tới `representative_dataset`/`supported_ops`/`inference_*_type` —
converter sẽ tự làm FP16.

## PyTorch (model buồn ngủ/landmark tự train)

Không có converter PyTorch → TFLite trực tiếp, phải qua ONNX:

```bash
pip install onnx onnx-tf onnx2tf
python -c "
import torch
model = torch.load('model.pt')
model.eval()
dummy = torch.randn(1, 3, 224, 224)  # đúng input shape thật của model
torch.onnx.export(model, dummy, 'model.onnx', opset_version=13)
"
onnx2tf -i model.onnx -o tflite_out -oiqt   # -oiqt = output INT8 quantized tflite
```

## YOLOv8 (nếu dùng cho phát hiện vật thể gây mất tập trung — điện thoại,...)

```bash
pip install ultralytics
yolo export model=best.pt format=tflite int8=True imgsz=224
```

## Sau khi có file .tflite (model KHÁC, không phải SVM ở trên)

1. Copy vào `mobile/assets/models/`, thêm đường dẫn vào mục `assets:` của
   `pubspec.yaml` (liệt kê từng file, không trỏ cả thư mục — thư mục này
   còn chứa file `.pkl` gốc không cần bundle vào app).
2. Chạy `flutter pub get` (để Flutter re-scan assets)
3. Kiểm tra input/output shape thật của model để viết lại
   `TFLiteModelService` cho khớp (xem cách `predictDrowsyProbability` hiện
   tại làm mẫu cho model SVM: input `[1, 28]`, output `[1]`).
4. Test nhanh bằng cách in `interpreter.getInputTensor(0).shape` và
   `getOutputTensor(0).shape` sau khi `load()` thành công để đối chiếu.
