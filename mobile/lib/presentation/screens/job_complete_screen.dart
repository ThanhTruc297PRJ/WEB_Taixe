import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';

import '../../services/vehicle_job_api.dart';

const _teal = Color(0xFF2A8B88);

/// Tài xế báo đã bảo trì / đăng kiểm xong: chụp ảnh hoá đơn hoặc tem (bắt
/// buộc), nhập số km đồng hồ, chi phí; đăng kiểm thêm kết quả + hạn tem mới.
/// Trả `true` qua Navigator.pop khi gửi thành công.
class JobCompleteScreen extends StatefulWidget {
  const JobCompleteScreen({super.key, required this.job});

  final VehicleJob job;

  @override
  State<JobCompleteScreen> createState() => _JobCompleteScreenState();
}

class _JobCompleteScreenState extends State<JobCompleteScreen> {
  final _formKey = GlobalKey<FormState>();
  final _api = VehicleJobApi();
  final _picker = ImagePicker();
  final _odometer = TextEditingController();
  final _cost = TextEditingController();
  final _roadFee = TextEditingController();
  final _note = TextEditingController();

  File? _photo;
  String _result = 'passed';
  DateTime? _newExpiry;
  bool _sending = false;

  VehicleJob get job => widget.job;

  @override
  void initState() {
    super.initState();
    if (job.currentOdometerKm != null) {
      _odometer.text = '${job.currentOdometerKm}';
    }
  }

  @override
  void dispose() {
    _odometer.dispose();
    _cost.dispose();
    _roadFee.dispose();
    _note.dispose();
    super.dispose();
  }

  void _toast(String text) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(text)));
  }

  Future<void> _pick(ImageSource source) async {
    try {
      final file = await _picker.pickImage(
        source: source,
        imageQuality: 80,
        maxWidth: 1600,
      );
      if (file != null) setState(() => _photo = File(file.path));
    } catch (e) {
      if (mounted) _toast('Không lấy được ảnh: $e');
    }
  }

  Future<void> _pickExpiry() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _newExpiry ?? DateTime(now.year + 1, now.month, now.day),
      firstDate: now,
      lastDate: DateTime(now.year + 5),
    );
    if (picked != null) setState(() => _newExpiry = picked);
  }

  double? _money(TextEditingController c) {
    final digits = c.text.replaceAll(RegExp(r'[^0-9]'), '');
    return digits.isEmpty ? null : double.parse(digits);
  }

  Future<void> _submit() async {
    if (_photo == null) {
      _toast(
        'Chụp ảnh ${job.isInspection ? 'tem đăng kiểm' : 'hoá đơn'} trước khi gửi',
      );
      return;
    }
    if (!_formKey.currentState!.validate()) return;
    if (job.isInspection && _result == 'passed' && _newExpiry == null) {
      _toast('Chọn ngày hết hạn tem mới');
      return;
    }
    setState(() => _sending = true);
    try {
      await _api.submit(
        job: job,
        photo: _photo!,
        odometer: int.parse(_odometer.text.replaceAll(RegExp(r'[^0-9]'), '')),
        note: _note.text.trim(),
        cost: job.isInspection ? null : _money(_cost),
        inspectionFee: job.isInspection ? _money(_cost) : null,
        roadFee: job.isInspection ? _money(_roadFee) : null,
        result: job.isInspection ? _result : null,
        newStickerExpiry: job.isInspection && _result == 'passed'
            ? _newExpiry
            : null,
      );
      if (!mounted) return;
      Navigator.of(context).pop(true);
    } catch (e) {
      if (!mounted) return;
      setState(() => _sending = false);
      _toast(e.toString());
    }
  }

  InputDecoration _decoration(String label, {String? suffix, String? hint}) =>
      InputDecoration(
        labelText: label,
        hintText: hint,
        suffixText: suffix,
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
      );

  @override
  Widget build(BuildContext context) {
    final digitsOnly = [FilteringTextInputFormatter.digitsOnly];
    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      appBar: AppBar(
        title: Text('Báo xong: ${job.title}'),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black87,
        elevation: 0,
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
          children: [
            if (job.plateNumber != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Text(
                  'Xe ${job.plateNumber}',
                  style: TextStyle(
                    fontSize: 15,
                    color: Colors.grey.shade700,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            _PhotoBox(
              photo: _photo,
              label: job.isInspection
                  ? 'Ảnh tem / giấy chứng nhận đăng kiểm'
                  : 'Ảnh hoá đơn gara',
              onCamera: () => _pick(ImageSource.camera),
              onGallery: () => _pick(ImageSource.gallery),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _odometer,
              keyboardType: TextInputType.number,
              inputFormatters: digitsOnly,
              decoration: _decoration('Số km trên đồng hồ', suffix: 'km'),
              validator: (v) {
                if (v == null || v.isEmpty) return 'Nhập số km hiện tại của xe';
                final km = int.parse(v);
                final current = job.currentOdometerKm;
                if (current != null && km < current) {
                  return 'Không được nhỏ hơn số km hiện tại ($current km)';
                }
                return null;
              },
            ),
            const SizedBox(height: 16),
            if (job.isInspection) ...[
              const Text(
                'Kết quả đăng kiểm',
                style: TextStyle(fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 8),
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment(value: 'passed', label: Text('Đạt')),
                  ButtonSegment(value: 'failed', label: Text('Không đạt')),
                ],
                selected: {_result},
                onSelectionChanged: (s) => setState(() => _result = s.first),
              ),
              const SizedBox(height: 16),
              if (_result == 'passed') ...[
                InkWell(
                  onTap: _pickExpiry,
                  borderRadius: BorderRadius.circular(14),
                  child: InputDecorator(
                    decoration: _decoration('Ngày hết hạn tem mới'),
                    child: Text(
                      _newExpiry == null
                          ? 'Chọn ngày'
                          : DateFormat('dd/MM/yyyy').format(_newExpiry!),
                      style: TextStyle(
                        color: _newExpiry == null
                            ? Colors.grey.shade500
                            : Colors.black87,
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
              ],
            ],
            TextFormField(
              controller: _cost,
              keyboardType: TextInputType.number,
              inputFormatters: digitsOnly,
              decoration: _decoration(
                job.isInspection ? 'Phí kiểm định' : 'Chi phí',
                suffix: 'đ',
              ),
              validator: (v) =>
                  (v == null || v.isEmpty) ? 'Nhập số tiền đã trả' : null,
            ),
            if (job.isInspection) ...[
              const SizedBox(height: 16),
              TextFormField(
                controller: _roadFee,
                keyboardType: TextInputType.number,
                inputFormatters: digitsOnly,
                decoration: _decoration(
                  'Phí bảo trì đường bộ (nếu có)',
                  suffix: 'đ',
                ),
              ),
            ],
            const SizedBox(height: 16),
            TextFormField(
              controller: _note,
              maxLines: 3,
              maxLength: 1000,
              decoration: _decoration(
                'Ghi chú (không bắt buộc)',
                hint: job.isInspection
                    ? 'VD: trạm yêu cầu thay đèn trước khi đăng kiểm lại'
                    : 'VD: thay thêm lọc gió',
              ),
            ),
            const SizedBox(height: 8),
            FilledButton(
              style: FilledButton.styleFrom(
                backgroundColor: _teal,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
              ),
              onPressed: _sending ? null : _submit,
              child: _sending
                  ? const SizedBox(
                      width: 22,
                      height: 22,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.5,
                        color: Colors.white,
                      ),
                    )
                  : const Text(
                      'Gửi cho quản lý xác nhận',
                      style: TextStyle(fontSize: 16),
                    ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PhotoBox extends StatelessWidget {
  const _PhotoBox({
    required this.photo,
    required this.label,
    required this.onCamera,
    required this.onGallery,
  });

  final File? photo;
  final String label;
  final VoidCallback onCamera;
  final VoidCallback onGallery;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey.shade300),
      ),
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(label, style: const TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 10),
          if (photo != null)
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Image.file(photo!, height: 220, fit: BoxFit.cover),
            )
          else
            Container(
              height: 140,
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(12),
              ),
              alignment: Alignment.center,
              child: Text(
                'Chưa có ảnh (bắt buộc)',
                style: TextStyle(color: Colors.grey.shade500),
              ),
            ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: onCamera,
                  icon: const Icon(Icons.photo_camera_rounded),
                  label: Text(photo == null ? 'Chụp ảnh' : 'Chụp lại'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: onGallery,
                  icon: const Icon(Icons.photo_library_rounded),
                  label: const Text('Thư viện'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
