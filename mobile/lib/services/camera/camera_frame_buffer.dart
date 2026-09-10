import 'dart:io';
import 'dart:ui';

import 'package:camera/camera.dart';
import 'package:google_mlkit_face_mesh_detection/google_mlkit_face_mesh_detection.dart';

/// Mở camera trước (tài xế) và chuyển từng khung hình CameraX/AVFoundation
/// thành [InputImage] để đưa vào các model AI (SUB-03/TASK-A02).
///
/// Dùng [ImageFormatGroup.nv21] (Android) / [ImageFormatGroup.bgra8888] (iOS)
/// khi mở camera để mỗi [CameraImage] chỉ có 1 plane duy nhất — tránh phải tự
/// ghép 3 plane của YUV_420_888, vốn là nguồn lỗi phổ biến nhất khi nối
/// `camera` với ML Kit.
class CameraFrameBuffer {
  CameraController? _controller;
  CameraDescription? _camera;
  bool _isStreaming = false;

  CameraController? get controller => _controller;
  bool get isReady => _controller?.value.isInitialized ?? false;
  bool get isStreaming => _isStreaming;

  Future<void> start({
    required void Function(InputImage image) onFrame,
    CameraLensDirection lensDirection = CameraLensDirection.front,
  }) async {
    final cameras = await availableCameras();
    final camera = cameras.firstWhere(
      (c) => c.lensDirection == lensDirection,
      orElse: () => cameras.first,
    );
    _camera = camera;

    final controller = CameraController(
      camera,
      ResolutionPreset.medium,
      enableAudio: false,
      imageFormatGroup:
          Platform.isAndroid ? ImageFormatGroup.nv21 : ImageFormatGroup.bgra8888,
    );
    _controller = controller;

    await controller.initialize();
    await _startStream(onFrame);
  }

  Future<void> _startStream(void Function(InputImage image) onFrame) async {
    final camera = _camera;
    if (camera == null) return;
    await _controller!.startImageStream((image) {
      final inputImage = _toInputImage(image, camera);
      if (inputImage != null) onFrame(inputImage);
    });
    _isStreaming = true;
  }

  /// Quay 1 clip [duration] giây, trả đường dẫn file .mp4. `camera` không cho
  /// vừa stream frame vừa quay nên phải tạm dừng stream; gọi [resumeStream]
  /// sau đó để nhận diện tiếp. Trả null nếu camera chưa sẵn sàng / lỗi.
  Future<String?> recordClip(Duration duration) async {
    final c = _controller;
    if (c == null || !c.value.isInitialized || c.value.isRecordingVideo) {
      return null;
    }
    try {
      if (_isStreaming) {
        await c.stopImageStream();
        _isStreaming = false;
      }
      await c.startVideoRecording();
      await Future.delayed(duration);
      final file = await c.stopVideoRecording();
      return file.path;
    } catch (_) {
      return null;
    }
  }

  /// Bật lại stream frame sau khi quay clip xong.
  Future<void> resumeStream({
    required void Function(InputImage image) onFrame,
  }) async {
    final c = _controller;
    if (c == null || !c.value.isInitialized || _isStreaming) return;
    await _startStream(onFrame);
  }

  Future<void> stop() async {
    final c = _controller;
    try {
      if (c != null && c.value.isRecordingVideo) {
        await c.stopVideoRecording();
      }
    } catch (_) {}
    if (_isStreaming) {
      try {
        await c?.stopImageStream();
      } catch (_) {}
      _isStreaming = false;
    }
    await c?.dispose();
    _controller = null;
    _camera = null;
  }

  InputImage? _toInputImage(CameraImage image, CameraDescription camera) {
    final rotation = Platform.isAndroid
        ? InputImageRotationValue.fromRawValue(camera.sensorOrientation)
        : InputImageRotation.rotation0deg;
    final format = Platform.isAndroid ? InputImageFormat.nv21 : InputImageFormat.bgra8888;
    if (rotation == null) return null;

    final plane = image.planes.first;
    return InputImage.fromBytes(
      bytes: plane.bytes,
      metadata: InputImageMetadata(
        size: Size(image.width.toDouble(), image.height.toDouble()),
        rotation: rotation,
        format: format,
        bytesPerRow: plane.bytesPerRow,
      ),
    );
  }
}
