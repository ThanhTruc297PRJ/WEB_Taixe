import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:geolocator/geolocator.dart';
import 'package:http/http.dart' as http;
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
  final TextEditingController _startController = TextEditingController();
  final TextEditingController _endController = TextEditingController();

  LatLng? _initialPosition;
  StreamSubscription<Position>? _positionStream;
  DateTime? _lastSpeedSentAt;

  final Set<Polyline> _polylines = {};
  final Set<Marker> _markers = {};
  bool _isLoadingRoute = false;

  static const LatLng _defaultLocation = LatLng(10.762622, 106.660172);
  static const _speedReportInterval = Duration(seconds: 10);

  void _maybeReportSpeed(Position position) {
    final now = DateTime.now();
    if (_lastSpeedSentAt != null &&
        now.difference(_lastSpeedSentAt!) < _speedReportInterval) {
      return;
    }
    final driverId = context.read<AuthViewModel>().account?.id;
    if (driverId == null) return;
    _lastSpeedSentAt = now;
    final speedKmh = position.speed * 3.6;
    _driverApi.updateSpeed(driverId, speedKmh).catchError((_) {});
  }

  @override
  void initState() {
    super.initState();
    _initLocation();
  }

  Future<void> _initLocation() async {
    print('=================================');
    print('[DEBUG MAP] BẮT ĐẦU TẢI MAP');
    try {
      print('[DEBUG MAP] Bước 1: Gọi kiểm tra Location Service...');
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      print('[DEBUG MAP] Trạng thái Service: $serviceEnabled');

      print('[DEBUG MAP] Bước 2: Gọi kiểm tra Quyền (Permission)...');
      LocationPermission permission = await Geolocator.checkPermission();
      print('[DEBUG MAP] Trạng thái Quyền ban đầu: $permission');

      if (permission == LocationPermission.denied) {
        print('[DEBUG MAP] Bước 3: Đang yêu cầu cấp quyền...');
        permission = await Geolocator.requestPermission();
        print('[DEBUG MAP] Trạng thái Quyền sau khi xin: $permission');
      }

      print('[DEBUG MAP] Bước 4: Đang gọi lệnh dò GPS (getCurrentPosition)...');
      Position position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: Duration(seconds: 5),
        ),
      );
      print(
        '[DEBUG MAP] Bước 5: THÀNH CÔNG! Đã lấy được tọa độ: ${position.latitude}, ${position.longitude}',
      );

      if (mounted) {
        setState(() {
          _initialPosition = LatLng(position.latitude, position.longitude);
        });
        _animateToPosition(_initialPosition!);
      }
    } catch (e) {
      print('[DEBUG MAP] 🛑 CÓ LỖI XẢY RA: $e');
      if (mounted) {
        setState(() => _initialPosition = _defaultLocation);
      }
    }
    print('=================================');

    // Chạy stream ở background
    _positionStream =
        Geolocator.getPositionStream(
          locationSettings: const LocationSettings(
            accuracy: LocationAccuracy.high,
            distanceFilter: 5,
          ),
        ).listen(
          (Position position) {
            if (mounted) {
              final newLatLng = LatLng(position.latitude, position.longitude);
              if (_polylines.isEmpty) {
                _animateToPosition(newLatLng);
              }
              _maybeReportSpeed(position);
            }
          },
          onError: (e) {
            print("[DEBUG MAP] Lỗi stream GPS: $e");
          },
        );
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

  Future<LatLng?> _getCoordinates(String address) async {
    final trimmed = address.trim();
    final coordRegex = RegExp(r'^-?\d+(\.\d+)?,\s*-?\d+(\.\d+)?$');
    if (coordRegex.hasMatch(trimmed)) {
      final parts = trimmed.split(',');
      return LatLng(
        double.parse(parts[0].trim()),
        double.parse(parts[1].trim()),
      );
    }
    final query =
        trimmed.toLowerCase().contains('vietnam') ||
            trimmed.toLowerCase().contains('việt nam')
        ? trimmed
        : '$trimmed, Vietnam';
    try {
      final url = Uri.parse(
        'https://nominatim.openstreetmap.org/search?q=${Uri.encodeComponent(query)}&format=json&limit=1&countrycodes=vn',
      );
      final response = await http.get(
        url,
        headers: {
          'User-Agent': 'DriverMonitoringSystemApp/1.0',
          'Accept-Language': 'vi,en',
        },
      );
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data is List && data.isNotEmpty) {
          return LatLng(
            double.parse(data[0]['lat']),
            double.parse(data[0]['lon']),
          );
        }
      }
    } catch (_) {}
    return null;
  }

  Future<void> _fetchRoute() async {
    if (_startController.text.trim().isEmpty ||
        _endController.text.trim().isEmpty) {
      return;
    }
    setState(() {
      _isLoadingRoute = true;
      _polylines.clear();
      _markers.clear();
    });

    try {
      LatLng? startLatLng;
      final startText = _startController.text.trim().toLowerCase();
      if ((startText == 'vị trí hiện tại' ||
              startText == 'my location' ||
              startText.isEmpty) &&
          _initialPosition != null) {
        startLatLng = _initialPosition;
      } else {
        startLatLng = await _getCoordinates(_startController.text);
      }

      final endLatLng = await _getCoordinates(_endController.text);

      if (startLatLng == null) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Không tìm thấy: ${_startController.text}')),
        );
        return;
      }
      if (endLatLng == null) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Không tìm thấy: ${_endController.text}')),
        );
        return;
      }

      final url = Uri.parse(
        'https://router.project-osrm.org/route/v1/driving/${startLatLng.longitude},${startLatLng.latitude};${endLatLng.longitude},${endLatLng.latitude}?geometries=geojson&overview=full',
      );
      final response = await http.get(url);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final routes = data['routes'] as List?;
        if (routes == null || routes.isEmpty) {
          throw Exception('Không có tuyến đường phù hợp');
        }

        final coords = routes[0]['geometry']['coordinates'] as List;
        final routePoints = coords
            .map(
              (c) => LatLng((c[1] as num).toDouble(), (c[0] as num).toDouble()),
            )
            .toList();

        setState(() {
          _polylines.add(
            Polyline(
              polylineId: const PolylineId('route'),
              points: routePoints,
              color: const Color(0xFF2A8B88),
              width: 5,
            ),
          );
          _markers.add(
            Marker(
              markerId: const MarkerId('start'),
              position: startLatLng!,
              infoWindow: const InfoWindow(title: 'Điểm bắt đầu'),
            ),
          );
          _markers.add(
            Marker(
              markerId: const MarkerId('end'),
              position: endLatLng,
              infoWindow: const InfoWindow(title: 'Điểm đến'),
              icon: BitmapDescriptor.defaultMarkerWithHue(
                BitmapDescriptor.hueCyan,
              ),
            ),
          );
        });

        final bounds = _boundsFromLatLngList(routePoints);
        final GoogleMapController mapController = await _controller.future;
        mapController.animateCamera(CameraUpdate.newLatLngBounds(bounds, 60));
      } else {
        throw Exception('Lỗi kết nối máy chủ OSRM (${response.statusCode})');
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Lỗi: $e')));
    } finally {
      if (mounted) setState(() => _isLoadingRoute = false);
    }
  }

  LatLngBounds _boundsFromLatLngList(List<LatLng> list) {
    double? x0, x1, y0, y1;
    for (final latLng in list) {
      if (x0 == null) {
        x0 = x1 = latLng.latitude;
        y0 = y1 = latLng.longitude;
      } else {
        if (latLng.latitude > x1!) x1 = latLng.latitude;
        if (latLng.latitude < x0) x0 = latLng.latitude;
        if (latLng.longitude > y1!) y1 = latLng.longitude;
        if (latLng.longitude < y0!) y0 = latLng.longitude;
      }
    }
    return LatLngBounds(
      northeast: LatLng(x1!, y1!),
      southwest: LatLng(x0!, y0!),
    );
  }

  @override
  void dispose() {
    _positionStream?.cancel();
    _startController.dispose();
    _endController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: _initialPosition == null
          ? const Center(
              child: CircularProgressIndicator(color: Color(0xFF2A8B88)),
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
                  polylines: _polylines,
                  markers: _markers,
                  padding: const EdgeInsets.only(top: 220),
                  onMapCreated: (GoogleMapController controller) {
                    if (!_controller.isCompleted) {
                      _controller.complete(controller);
                    }
                  },
                ),
                Positioned(
                  top: MediaQuery.of(context).padding.top + 56,
                  left: 16,
                  right: 16,
                  child: Container(
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(
                        color: Colors.white.withValues(alpha: 0.9),
                        width: 1.5,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.08),
                          blurRadius: 24,
                          offset: const Offset(0, 8),
                        ),
                      ],
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          TextField(
                            controller: _startController,
                            style: const TextStyle(
                              color: Colors.black87,
                              fontWeight: FontWeight.w500,
                            ),
                            decoration: InputDecoration(
                              hintText: 'Điểm đi (hoặc "Vị trí hiện tại")',
                              hintStyle: TextStyle(
                                color: Colors.grey.shade400,
                                fontWeight: FontWeight.normal,
                              ),
                              prefixIcon: const Icon(
                                Icons.my_location,
                                color: Color(0xFF2A8B88),
                              ),
                              suffixIcon: IconButton(
                                icon: const Icon(
                                  Icons.gps_fixed,
                                  color: Color(0xFF2A8B88),
                                  size: 20,
                                ),
                                onPressed: () =>
                                    _startController.text = 'Vị trí hiện tại',
                              ),
                              filled: true,
                              fillColor: const Color(0xFFF3F4F6),
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(16),
                                borderSide: BorderSide.none,
                              ),
                              contentPadding: const EdgeInsets.symmetric(
                                horizontal: 16,
                                vertical: 14,
                              ),
                            ),
                          ),
                          const SizedBox(height: 12),
                          TextField(
                            controller: _endController,
                            style: const TextStyle(
                              color: Colors.black87,
                              fontWeight: FontWeight.w500,
                            ),
                            decoration: InputDecoration(
                              hintText: 'Nhập điểm đến (VD: Tân Bình)',
                              hintStyle: TextStyle(
                                color: Colors.grey.shade400,
                                fontWeight: FontWeight.normal,
                              ),
                              prefixIcon: const Icon(
                                Icons.location_on,
                                color: Colors.redAccent,
                              ),
                              filled: true,
                              fillColor: const Color(0xFFF3F4F6),
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(16),
                                borderSide: BorderSide.none,
                              ),
                              contentPadding: const EdgeInsets.symmetric(
                                horizontal: 16,
                                vertical: 14,
                              ),
                            ),
                          ),
                          const SizedBox(height: 16),
                          Container(
                            decoration: BoxDecoration(
                              gradient: const LinearGradient(
                                colors: [Color(0xFF2A8B88), Color(0xFF175452)],
                              ),
                              borderRadius: BorderRadius.circular(16),
                            ),
                            child: SizedBox(
                              width: double.infinity,
                              height: 50,
                              child: ElevatedButton(
                                onPressed: _isLoadingRoute ? null : _fetchRoute,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.transparent,
                                  shadowColor: Colors.transparent,
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(16),
                                  ),
                                ),
                                child: _isLoadingRoute
                                    ? const SizedBox(
                                        height: 24,
                                        width: 24,
                                        child: CircularProgressIndicator(
                                          strokeWidth: 2.5,
                                          color: Colors.white,
                                        ),
                                      )
                                    : const Text(
                                        'TÌM ĐƯỜNG',
                                        style: TextStyle(
                                          color: Colors.white,
                                          fontWeight: FontWeight.bold,
                                          letterSpacing: 1.2,
                                        ),
                                      ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
    );
  }
}
