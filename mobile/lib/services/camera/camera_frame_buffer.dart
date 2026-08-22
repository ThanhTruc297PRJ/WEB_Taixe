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
  bool _isStreaming = false;

  CameraController? get controller => _controller;
  bool get isReady => _controller?.value.isInitialized ?? false;

  Future<void> start({
    required void Function(InputImage image) onFrame,
    CameraLensDirection lensDirection = CameraLensDirection.front,
  }) async {
    final cameras = await availableCameras();
    final camera = cameras.firstWhere(
      (c) => c.lensDirection == lensDirection,
      orElse: () => cameras.first,
    );

    final controller = CameraController(
      camera,
      ResolutionPreset.medium,
      enableAudio: false,
      imageFormatGroup:
          Platform.isAndroid ? ImageFormatGroup.nv21 : ImageFormatGroup.bgra8888,
    );
    _controller = controller;

    await controller.initialize();
    await controller.startImageStream((image) {
      final inputImage = _toInputImage(image, camera);
      if (inputImage != null) onFrame(inputImage);
    });
    _isStreaming = true;
  }

  Future<void> stop() async {
    if (_isStreaming) {
      await _controller?.stopImageStream();
      _isStreaming = false;
    }
    await _controller?.dispose();
    _controller = null;
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
