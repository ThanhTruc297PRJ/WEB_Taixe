import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:geolocator/geolocator.dart';
import 'package:geocoding/geocoding.dart';
import 'dart:io';

import '../../services/api_client.dart';
import '../../services/driver_report_api.dart';

class ReportScreen extends StatefulWidget {
  const ReportScreen({super.key});

  @override
  State<ReportScreen> createState() => _ReportScreenState();
}

class _ReportScreenState extends State<ReportScreen> {
  File? _selectedImage;
  final ImagePicker _picker = ImagePicker();
  final TextEditingController _noteController = TextEditingController();
  final DriverReportApi _reportApi = DriverReportApi();
  bool _submitting = false;
  String? _hotline;

  @override
  void initState() {
    super.initState();
    _loadHotline();
  }

  Future<void> _loadHotline() async {
    try {
      final hotline = await _reportApi.companyHotline();
      if (mounted) setState(() => _hotline = hotline);
    } catch (_) {
      // Mất mạng / lỗi tạm -> nút Cứu hộ tự báo chưa có số, không chặn màn hình.
    }
  }

  void _toast(String text) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(text)));
  }

  Future<void> _pickImage(ImageSource source) async {
    try {
      final XFile? pickedFile = await _picker.pickImage(
        source: source,
        imageQuality: 80,
        maxWidth: 1600,
      );

      if (pickedFile != null) {
        setState(() {
          _selectedImage = File(pickedFile.path);
        });
      }
    } catch (e) {
      if (!mounted) return;
      _toast('Không thể lấy ảnh: $e');
    }
  }

  void _showImageSourceOptions() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                'Chọn nguồn ảnh',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                ),
              ),
              const SizedBox(height: 20),
              ListTile(
                leading: Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: const Color(0xFF2A8B88).withValues(alpha: 0.1),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.camera_alt_rounded,
                    color: Color(0xFF2A8B88),
                  ),
                ),
                title: const Text(
                  'Chụp ảnh mới',
                  style: TextStyle(
                    fontWeight: FontWeight.w600,
                    color: Colors.black87,
                  ),
                ),
                onTap: () {
                  Navigator.pop(context);
                  _pickImage(ImageSource.camera);
                },
              ),
              const Divider(height: 1),
              ListTile(
                leading: Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: const Color(0xFF2A8B88).withValues(alpha: 0.1),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.photo_library_rounded,
                    color: Color(0xFF2A8B88),
                  ),
                ),
                title: const Text(
                  'Chọn từ thư viện',
                  style: TextStyle(
                    fontWeight: FontWeight.w600,
                    color: Colors.black87,
                  ),
                ),
                onTap: () {
                  Navigator.pop(context);
                  _pickImage(ImageSource.gallery);
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<({double? lat, double? lng, String? address})> _getLocation() async {
    try {
      var perm = await Geolocator.checkPermission();
      if (perm == LocationPermission.denied) {
        perm = await Geolocator.requestPermission();
      }
      if (perm == LocationPermission.denied ||
          perm == LocationPermission.deniedForever) {
        return (lat: null, lng: null, address: null);
      }
      final pos = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: Duration(seconds: 6),
        ),
      );
      final placemarks = await Geocoding().placemarkFromCoordinates(
        pos.latitude,
        pos.longitude,
      );
      final p = placemarks.isNotEmpty ? placemarks.first : null;
      final parts = [
        p?.street,
        p?.subLocality,
        p?.locality,
        p?.administrativeArea,
      ].whereType<String>().where((s) => s.isNotEmpty).toList();
      final addr = parts.join(', ');
      return (lat: pos.latitude, lng: pos.longitude, address: addr);
    } catch (_) {
      return (lat: null, lng: null, address: null);
    }
  }

  Future<void> _submitReport() async {
    final note = _noteController.text.trim();
    if (note.isEmpty && _selectedImage == null) {
      _toast('Nhập mô tả hoặc đính kèm ảnh trước khi gửi');
      return;
    }
    FocusScope.of(context).unfocus();
    setState(() => _submitting = true);
    try {
      final loc = await _getLocation();
      await _reportApi.submit(
        note: note,
        photo: _selectedImage,
        latitude: loc.lat,
        longitude: loc.lng,
        address: loc.address,
      );
      if (!mounted) return;
      _toast('Đã gửi báo cáo tới công ty');
      setState(() {
        _selectedImage = null;
        _noteController.clear();
      });
    } on ApiException catch (e) {
      if (mounted) _toast(e.message);
    } catch (_) {
      if (mounted) _toast('Không gửi được báo cáo — kiểm tra kết nối mạng rồi thử lại');
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  void _callHotline() {
    final hotline = _hotline;
    if (hotline == null || hotline.isEmpty) {
      _toast('Công ty chưa cài số cứu hộ — dùng các số khẩn cấp bên cạnh');
      return;
    }
    _triggerEmergency('Cứu hộ của công ty', hotline.replaceAll(RegExp(r'[ .]'), ''));
  }

  // Hàm gọi điện thoại trực tiếp
  Future<void> _triggerEmergency(String title, String phoneNumber) async {
    final Uri launchUri = Uri(scheme: 'tel', path: phoneNumber);
    try {
      if (await canLaunchUrl(launchUri)) {
        await launchUrl(launchUri);
      } else {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Không thể thực hiện cuộc gọi đến $title ($phoneNumber)',
            ),
          ),
        );
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Lỗi gọi điện: $e')));
    }
  }

  @override
  void dispose() {
    _noteController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(16, 105, 16, 120),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Mô tả tình trạng',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Colors.black87,
              ),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _noteController,
              maxLines: 4,
              style: const TextStyle(color: Colors.black87),
              decoration: InputDecoration(
                hintText: 'Nhập thông tin sự cố (ví dụ: hỏng lốp, va chạm...)',
                hintStyle: TextStyle(color: Colors.grey.shade400),
                filled: true,
                fillColor: Colors.white,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: BorderSide.none,
                ),
                contentPadding: const EdgeInsets.all(16),
              ),
            ),
            const SizedBox(height: 20),

            InkWell(
              onTap: _showImageSourceOptions,
              borderRadius: BorderRadius.circular(16),
              child: Container(
                height: 180,
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.03),
                      blurRadius: 10,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: _selectedImage != null
                    ? Stack(
                        fit: StackFit.expand,
                        children: [
                          ClipRRect(
                            borderRadius: BorderRadius.circular(16),
                            child: Image.file(
                              _selectedImage!,
                              fit: BoxFit.cover,
                            ),
                          ),
                          Positioned(
                            top: 8,
                            right: 8,
                            child: CircleAvatar(
                              backgroundColor: Colors.black54,
                              radius: 16,
                              child: IconButton(
                                icon: const Icon(
                                  Icons.close,
                                  size: 16,
                                  color: Colors.white,
                                ),
                                onPressed: () =>
                                    setState(() => _selectedImage = null),
                              ),
                            ),
                          ),
                        ],
                      )
                    : Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            padding: const EdgeInsets.all(14),
                            decoration: BoxDecoration(
                              color: const Color(
                                0xFF2A8B88,
                              ).withValues(alpha: 0.1),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(
                              Icons.camera_alt_rounded,
                              size: 28,
                              color: Color(0xFF2A8B88),
                            ),
                          ),
                          const SizedBox(height: 10),
                          Text(
                            'Chụp ảnh hoặc chọn từ thư viện',
                            style: TextStyle(
                              color: Colors.grey.shade600,
                              fontWeight: FontWeight.w500,
                              fontSize: 13,
                            ),
                          ),
                        ],
                      ),
              ),
            ),

            const SizedBox(height: 24),
            SizedBox(
              height: 52,
              child: ElevatedButton(
                onPressed: _submitting ? null : _submitReport,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF2A8B88),
                  foregroundColor: Colors.white,
                  disabledBackgroundColor: const Color(
                    0xFF2A8B88,
                  ).withValues(alpha: 0.6),
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
                child: _submitting
                    ? const SizedBox(
                        width: 22,
                        height: 22,
                        child: CircularProgressIndicator(
                          strokeWidth: 2.5,
                          color: Colors.white,
                        ),
                      )
                    : const Text(
                        'Gửi Báo Cáo',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 0.5,
                        ),
                      ),
              ),
            ),

            const SizedBox(height: 28),
            Row(
              children: [
                const Icon(
                  Icons.emergency_rounded,
                  color: Colors.redAccent,
                  size: 20,
                ),
                const SizedBox(width: 8),
                Text(
                  'Hỗ trợ khẩn cấp nhanh (SOS)',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                    color: Colors.grey.shade700,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: _buildSosButton(
                    title: 'Cấp cứu',
                    subtitle: '115',
                    icon: Icons.medical_services_rounded,
                    color: Colors.redAccent,
                    onTap: () => _triggerEmergency('Cấp cứu', '115'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _buildSosButton(
                    title: 'Cứu hộ',
                    subtitle: (_hotline?.isNotEmpty ?? false)
                        ? _hotline!
                        : 'Chưa cài số',
                    icon: Icons.car_repair_rounded,
                    color: Colors.orange,
                    onTap: _callHotline,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: _buildSosButton(
                    title: 'CSGT',
                    subtitle: '113',
                    icon: Icons.local_police_rounded,
                    color: Colors.blueAccent,
                    onTap: () =>
                        _triggerEmergency('Cảnh sát giao thông', '113'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _buildSosButton(
                    title: 'Cứu hỏa',
                    subtitle: '114',
                    icon: Icons.fire_truck_rounded,
                    color: Colors.deepOrange,
                    onTap: () => _triggerEmergency('Cứu hỏa', '114'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSosButton({
    required String title,
    required String subtitle,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: color.withValues(alpha: 0.2)),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.02),
                blurRadius: 8,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, color: color, size: 24),
              const SizedBox(height: 6),
              Text(
                title,
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 13,
                  color: Colors.black87,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                subtitle,
                style: TextStyle(fontSize: 11, color: Colors.grey.shade500),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
