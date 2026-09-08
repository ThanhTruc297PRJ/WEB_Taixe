import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:geolocator/geolocator.dart';

class MapScreen extends StatefulWidget {
  const MapScreen({super.key});

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  final Completer<GoogleMapController> _controller = Completer();
  LatLng? _initialPosition;
  StreamSubscription<Position>? _positionStream;

  static const LatLng _defaultLocation = LatLng(10.762622, 106.660172);

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
