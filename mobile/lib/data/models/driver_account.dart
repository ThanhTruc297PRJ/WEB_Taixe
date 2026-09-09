enum DriverAccountStatus { pending, active, inactive, rejected, unknown }

DriverAccountStatus _parseStatus(String? s) {
  switch (s) {
    case 'pending':
      return DriverAccountStatus.pending;
    case 'active':
      return DriverAccountStatus.active;
    case 'inactive':
      return DriverAccountStatus.inactive;
    case 'rejected':
      return DriverAccountStatus.rejected;
    default:
      return DriverAccountStatus.unknown;
  }
}

/// Hồ sơ tài xế trả về từ `GET /drivers/me`.
class DriverAccount {
  DriverAccount({
    required this.id,
    required this.name,
    required this.phone,
    required this.licenseNumber,
    required this.status,
    this.rejectReason,
  });

  final String id;
  final String name;
  final String phone;
  final String licenseNumber;
  final DriverAccountStatus status;
  final String? rejectReason;

  factory DriverAccount.fromJson(Map<String, dynamic> j) => DriverAccount(
        id: j['id'] as String,
        name: j['name'] as String? ?? '',
        phone: j['phone'] as String? ?? '',
        licenseNumber: j['license_number'] as String? ?? '',
        status: _parseStatus(j['status'] as String?),
        rejectReason: j['reject_reason'] as String?,
      );
}
