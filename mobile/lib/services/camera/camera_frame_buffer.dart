import 'dart:io';
import 'dart:ui';

import 'package:camera/camera.dart';
import 'package:google_mlkit_face_mesh_detection/google_mlkit_face_mesh_detection.dart';

import 'frame_source.dart';

/// Camera trước của điện thoại.
class CameraFrameBuffer implements FrameSource {
  CameraController? _controller;
  CameraDescription? _camera;
  bool _isStreaming = false;

  CameraController? get controller => _controller;
  bool get isReady => _controller?.value.isInitialized ?? false;
  bool get isStreaming => _isStreaming;

  @override
  bool get isExternal => false;

  @override
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
      imageFormatGroup: Platform.isAndroid
          ? ImageFormatGroup.nv21
          : ImageFormatGroup.bgra8888,
    );
    _controller = controller;

    await controller.initialize();
    await _startStream(onFrame);
  }

  @override
  Future<void> switchCamera({
    required void Function(InputImage image) onFrame,
  }) async {
    final cameras = await availableCameras();
    if (cameras.isEmpty) return;

    int currentIndex = cameras.indexWhere((c) => c.name == _camera?.name);
    final nextCamera = cameras[(currentIndex + 1) % cameras.length];

    await stop();

    _camera = nextCamera;
    final controller = CameraController(
      nextCamera,
      ResolutionPreset.medium,
      enableAudio: false,
      imageFormatGroup: Platform.isAndroid
          ? ImageFormatGroup.nv21
          : ImageFormatGroup.bgra8888,
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

  @override
  Future<String?> capturePhoto() async {
    final c = _controller;
    if (c == null || !c.value.isInitialized || c.value.isRecordingVideo) {
      return null;
    }
    try {
      if (_isStreaming) {
        await c.stopImageStream();
        _isStreaming = false;
      }
      final file = await c.takePicture();
      return file.path;
    } catch (_) {
      return null;
    }
  }

  @override
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

  @override
  Future<void> resumeStream({
    required void Function(InputImage image) onFrame,
  }) async {
    final c = _controller;
    if (c == null || !c.value.isInitialized || _isStreaming) return;
    await _startStream(onFrame);
  }

  @override
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
    final format = Platform.isAndroid
        ? InputImageFormat.nv21
        : InputImageFormat.bgra8888;
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
