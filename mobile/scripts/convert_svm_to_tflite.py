"""Convert assets/models/best_model_svm_window.pkl (sklearn Pipeline:
RobustScaler -> CalibratedClassifierCV(SVC, cv=2)) into a .tflite that
tflite_flutter can load directly.

Why not just export to ONNX/TFLite with skl2onnx + onnx2tf?
That path was tried first: it converts, but skl2onnx maps SVC/RobustScaler
to the ai.onnx.ml ops (Scaler, SVMClassifier), and onnx2tf turns those into
TFLite "custom ops" instead of standard builtin ops. tflite_flutter (like
any stock TFLite runtime) has no kernel for them and fails at
allocate_tensors() with "Encountered unresolved custom op: ONNX_SCALER".

Instead, this script re-derives the exact math sklearn runs at inference
(RobustScaler -> RBF-kernel SVM decision function -> Platt/sigmoid
calibration -> average across the cv folds) using only primitive TF ops
(sub/div/exp/matmul/sigmoid), which the TFLite converter maps to plain
builtin ops. Output is numerically verified against the original sklearn
pipeline's predict_proba before being written to disk (see bottom of file).

Requirements (not part of the app's own requirements — only needed to run
this script once, on a dev machine): joblib, scikit-learn, tensorflow, numpy.

Usage:
    pip install joblib scikit-learn tensorflow numpy
    python scripts/convert_svm_to_tflite.py
"""

import warnings

warnings.filterwarnings("ignore")

import pathlib

import joblib
import numpy as np
import tensorflow as tf

MODEL_DIR = pathlib.Path(__file__).resolve().parent.parent / "assets" / "models"
SOURCE_PKL = MODEL_DIR / "best_model_svm_window.pkl"
OUTPUT_TFLITE = MODEL_DIR / "drowsiness_model.tflite"


def load_fold_params(model):
    scaler = model.named_steps["scaler"]
    calib = model.named_steps["svm"]

    center = tf.constant(scaler.center_, dtype=tf.float32)
    scale = tf.constant(scaler.scale_, dtype=tf.float32)

    folds = []
    for cc in calib.calibrated_classifiers_:
        est = cc.estimator
        calibrator = cc.calibrators[0]
        folds.append(
            {
                "sv": tf.constant(est.support_vectors_, dtype=tf.float32),
                "dual_coef": tf.constant(est.dual_coef_[0], dtype=tf.float32),
                "intercept": tf.constant(est.intercept_[0], dtype=tf.float32),
                "gamma": tf.constant(est._gamma, dtype=tf.float32),
                "a": tf.constant(calibrator.a_, dtype=tf.float32),
                "b": tf.constant(calibrator.b_, dtype=tf.float32),
            }
        )
    return center, scale, folds


def build_module(center, scale, folds, n_features):
    class DrowsinessSVM(tf.Module):
        @tf.function(
            input_signature=[
                tf.TensorSpec(shape=[1, n_features], dtype=tf.float32, name="features")
            ]
        )
        def __call__(self, x):
            x_scaled = (x - center) / scale

            probs = []
            for f in folds:
                diff = tf.expand_dims(x_scaled, axis=1) - tf.expand_dims(f["sv"], axis=0)
                sqdist = tf.reduce_sum(tf.square(diff), axis=-1)
                kernel = tf.exp(-f["gamma"] * sqdist)
                decision = tf.reduce_sum(kernel * f["dual_coef"], axis=-1) + f["intercept"]
                prob = tf.sigmoid(-(f["a"] * decision + f["b"]))
                probs.append(prob)

            drowsy_prob = tf.add_n(probs) / float(len(folds))
            return {"drowsy_probability": drowsy_prob}

    return DrowsinessSVM()


def main():
    model = joblib.load(SOURCE_PKL)
    n_features = model.n_features_in_

    center, scale, folds = load_fold_params(model)
    module = build_module(center, scale, folds, n_features)
    concrete_fn = module.__call__.get_concrete_function()

    converter = tf.lite.TFLiteConverter.from_concrete_functions([concrete_fn], module)
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
    tflite_model = converter.convert()

    OUTPUT_TFLITE.write_bytes(tflite_model)
    print(f"Wrote {OUTPUT_TFLITE} ({len(tflite_model)} bytes)")

    # Numeric sanity check: TFLite output must match sklearn's predict_proba.
    rng = np.random.default_rng(0)
    X = rng.normal(size=(20, n_features)).astype(np.float32)
    sk_proba = model.predict_proba(X)[:, 1]

    interp = tf.lite.Interpreter(model_path=str(OUTPUT_TFLITE))
    interp.allocate_tensors()
    in_detail = interp.get_input_details()[0]
    out_detail = interp.get_output_details()[0]

    tfl_proba = np.zeros(len(X), dtype=np.float32)
    for i in range(len(X)):
        interp.set_tensor(in_detail["index"], X[i : i + 1])
        interp.invoke()
        tfl_proba[i] = interp.get_tensor(out_detail["index"])[0]

    max_diff = float(np.max(np.abs(sk_proba - tfl_proba)))
    print(f"max abs diff vs sklearn predict_proba: {max_diff:.2e}")
    if max_diff > 1e-4:
        raise SystemExit("Conversion mismatch too large — do not ship this .tflite")


if __name__ == "__main__":
    main()
