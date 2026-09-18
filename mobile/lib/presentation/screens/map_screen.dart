import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:geolocator/geolocator.dart';
import 'package:provider/provider.dart';

import '../viewmodels/auth_view_model.dart';
import '../../services/driver_api.dart';

class MapScreen extends StatefulWidget {
  const MapScreen({super.key});

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  final Completer<GoogleMapController> _controller = Completer();
  final _driverApi = DriverApi();
  LatLng? _initialPosition;
  StreamSubscription<Position>? _positionStream;
  DateTime? _lastSpeedSentAt;

  static const LatLng _defaultLocation = LatLng(10.762622, 106.660172);
  static const _speedReportInterval = Duration(seconds: 10);

  /// Báo tốc độ lên web admin — điều tiết (không gửi mỗi lần vị trí đổi, chỉ
  /// tối đa 1 lần/10s) để đỡ tốn pin/mạng và không vượt rate limit backend.
  /// CHỈ chạy khi màn này đang mở (app foreground) — không có dịch vụ nền.
  void _maybeReportSpeed(Position position) {
    final now = DateTime.now();
    if (_lastSpeedSentAt != null &&
        now.difference(_lastSpeedSentAt!) < _speedReportInterval) {
      return;
    }
    final driverId = context.read<AuthViewModel>().account?.id;
    if (driverId == null) return;
    _lastSpeedSentAt = now;
    final speedKmh = position.speed * 3.6; // m/s -> km/h
    _driverApi.updateSpeed(driverId, speedKmh).catchError((_) {
      // Lỗi mạng lúc báo tốc độ không cần làm phiền tài xế — bỏ qua, lần
      // cập nhật vị trí kế tiếp sẽ tự thử lại.
    });
  }

  @override
  void initState() {
    super.initState();
    _initLocation();
  }

  Future<void> _initLocation() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      await Geolocator.openLocationSettings();
    }

    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        setState(() => _initialPosition = _defaultLocation);
        return;
      }
    }

    if (permission == LocationPermission.deniedForever) {
      setState(() => _initialPosition = _defaultLocation);
      return;
    }

    try {
      Position position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
        ),
        timeLimit: const Duration(seconds: 5),
      );
      setState(() {
        _initialPosition = LatLng(position.latitude, position.longitude);
      });
      _animateToPosition(_initialPosition!);
    } catch (_) {
      setState(() => _initialPosition = _defaultLocation);
    }

    _positionStream =
        Geolocator.getPositionStream(
          locationSettings: const LocationSettings(
            accuracy: LocationAccuracy.high,
            distanceFilter: 5,
          ),
        ).listen((Position position) {
          final newLatLng = LatLng(position.latitude, position.longitude);
          _animateToPosition(newLatLng);
          _maybeReportSpeed(position);
        });
  }

  Future<void> _animateToPosition(LatLng target) async {
    if (_controller.isCompleted) {
      final GoogleMapController mapController = await _controller.future;
      mapController.animateCamera(
        CameraUpdate.newCameraPosition(
          CameraPosition(target: target, zoom: 17.0, tilt: 30),
        ),
      );
    }
  }

  @override
  void dispose() {
    _positionStream?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _initialPosition == null
          ? const Center(
              child: CircularProgressIndicator(color: Colors.cyanAccent),
            )
          : Stack(
              children: [
                GoogleMap(
                  initialCameraPosition: CameraPosition(
                    target: _initialPosition!,
                    zoom: 17.0,
                  ),
                  myLocationEnabled: true,
                  myLocationButtonEnabled: true,
                  compassEnabled: true,
                  trafficEnabled: true,
                  zoomControlsEnabled: false,
                  onMapCreated: (GoogleMapController controller) {
                    if (!_controller.isCompleted) {
                      _controller.complete(controller);
                    }
                  },
                ),
              ],
            ),
    );
  }
}
