"""Convert assets/models/mlp_feature_result.pkl (sklearn Pipeline:
StandardScaler -> MLPClassifier(128, 64, 32), relu hidden, logistic output)
into a .tflite that tflite_flutter can load directly.

Đây là model "MLP-Feature" từ notebook tcg-paper.ipynb — thay cho model SVM
cũ. Nhận 11 đặc trưng (xem FEATURE_COLS), trả về xác suất buồn ngủ [0, 1].

Khác `convert_svm_to_tflite.py`: MLP chỉ là chuỗi matmul + relu + sigmoid,
convert thẳng ra builtin op không cần dựng lại RBF kernel. Vẫn verify output
khớp `predict_proba` gốc trước khi ghi file.

PHẦN 1 (chỉ convert + verify): script này ghi ra `drowsiness_mlp.tflite` và
`model_meta_mlp.json` — KHÔNG đè lên model đang chạy. Việc nối vào Flutter
(đổi tên file, sửa feature extraction) làm ở phần 2.

Requirements (chỉ chạy 1 lần trên máy dev): joblib, scikit-learn,
tensorflow, numpy.

Usage:
    python scripts/convert_mlp_to_tflite.py
"""

import json
import warnings

warnings.filterwarnings("ignore")

import pathlib

import joblib
import numpy as np
import tensorflow as tf

MODEL_DIR = pathlib.Path(__file__).resolve().parent.parent / "assets" / "models"
SOURCE_PKL = MODEL_DIR / "mlp_feature_result.pkl"
OUTPUT_TFLITE = MODEL_DIR / "drowsiness_mlp.tflite"
OUTPUT_META = MODEL_DIR / "model_meta_mlp.json"

# Hằng số từ CELL 1 (config) của notebook — phải khớp khi tính đặc trưng
# phía Flutter ở phần 2.
FEATURE_COLS = [
    "ear",
    "mar",
    "ear_roll_mean",
    "ear_roll_std",
    "mar_roll_mean",
    "mar_roll_std",
    "mar_diff",
    "ear_mar_ratio_roll",
    "perclos_true",
    "blink_rate",
    "head_tilt_roll_std",
]
ROLLING_WINDOW = 5
PERCLOS_WINDOW = 30
EAR_BLINK_THRESH = 0.21
EMA_BETA = 0.70
EMA_GAP_RESET = 20
THRESHOLD = 0.50
EFF_FPS = 6.0


def build_module(scaler, mlp, n_features):
    mean = tf.constant(scaler.mean_, dtype=tf.float32)
    scale = tf.constant(scaler.scale_, dtype=tf.float32)
    weights = [tf.constant(w, dtype=tf.float32) for w in mlp.coefs_]
    biases = [tf.constant(b, dtype=tf.float32) for b in mlp.intercepts_]

    class DrowsinessMLP(tf.Module):
        @tf.function(
            input_signature=[
                tf.TensorSpec(shape=[1, n_features], dtype=tf.float32, name="features")
            ]
        )
        def __call__(self, x):
            h = (x - mean) / scale
            # các lớp ẩn: relu(h @ W + b)
            for w, b in zip(weights[:-1], biases[:-1]):
                h = tf.nn.relu(tf.matmul(h, w) + b)
            # lớp ra: sigmoid(h @ W + b) -> P(buồn ngủ)
            logit = tf.matmul(h, weights[-1]) + biases[-1]
            drowsy_prob = tf.reshape(tf.sigmoid(logit), [1])
            return {"drowsy_probability": drowsy_prob}

    return DrowsinessMLP()


def main():
    bundle = joblib.load(SOURCE_PKL)
    pipe = bundle["model"]
    feature_cols = bundle.get("feature_cols", FEATURE_COLS)
    if list(feature_cols) != FEATURE_COLS:
        raise SystemExit(
            f"feature_cols trong pkl khác hằng số script:\n"
            f"  pkl:    {list(feature_cols)}\n"
            f"  script: {FEATURE_COLS}"
        )

    scaler = pipe.named_steps["scaler"]
    mlp = pipe.named_steps["mlp"]
    n_features = pipe.n_features_in_
    assert n_features == len(FEATURE_COLS), (n_features, len(FEATURE_COLS))

    module = build_module(scaler, mlp, n_features)
    concrete_fn = module.__call__.get_concrete_function()

    converter = tf.lite.TFLiteConverter.from_concrete_functions([concrete_fn], module)
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
    tflite_model = converter.convert()
    OUTPUT_TFLITE.write_bytes(tflite_model)
    print(f"Wrote {OUTPUT_TFLITE.name} ({len(tflite_model)} bytes)")

    # ── Verify: TFLite output phải khớp predict_proba của sklearn ──
    rng = np.random.default_rng(0)
    # trộn cả input ngẫu nhiên thô lẫn input quanh vùng dữ liệu thật
    X_rand = rng.normal(size=(30, n_features)).astype(np.float32)
    X_real = (scaler.mean_ + rng.normal(size=(30, n_features)) * scaler.scale_).astype(
        np.float32
    )
    X = np.vstack([X_rand, X_real])
    sk_proba = pipe.predict_proba(X)[:, 1]

    interp = tf.lite.Interpreter(model_path=str(OUTPUT_TFLITE))
    interp.allocate_tensors()
    in_detail = interp.get_input_details()[0]
    out_detail = interp.get_output_details()[0]
    print("input shape :", in_detail["shape"], "| output shape:", out_detail["shape"])

    tfl_proba = np.zeros(len(X), dtype=np.float32)
    for i in range(len(X)):
        interp.set_tensor(in_detail["index"], X[i : i + 1])
        interp.invoke()
        tfl_proba[i] = interp.get_tensor(out_detail["index"]).reshape(-1)[0]

    max_diff = float(np.max(np.abs(sk_proba - tfl_proba)))
    print(f"max abs diff vs sklearn predict_proba: {max_diff:.2e}")
    if max_diff > 1e-4:
        raise SystemExit("Conversion mismatch too large — do not ship this .tflite")

    # ── Ghi metadata cho phần 2 ──
    meta = {
        "winner": "MLP-Feature",
        "source_metrics": bundle.get("metrics", {}),
        "threshold": THRESHOLD,
        "rolling_window": ROLLING_WINDOW,
        "perclos_window": PERCLOS_WINDOW,
        "ear_blink_thresh": EAR_BLINK_THRESH,
        "ema_beta": EMA_BETA,
        "ema_gap_reset": EMA_GAP_RESET,
        "eff_fps": EFF_FPS,
        "needs_baseline_calibration": False,
        "feature_cols": FEATURE_COLS,
    }
    OUTPUT_META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUTPUT_META.name}")
    print("\nOK - conversion verified, ready for part 2 (wire into Flutter).")


if __name__ == "__main__":
    main()
