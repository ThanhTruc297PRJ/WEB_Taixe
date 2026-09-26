import 'dart:io';

import 'package:flutter/material.dart';
import 'package:animate_do/animate_do.dart';
import 'package:fluentui_system_icons/fluentui_system_icons.dart';
import 'package:provider/provider.dart';
import 'package:image_picker/image_picker.dart';
import 'package:firebase_storage/firebase_storage.dart';
import 'package:firebase_auth/firebase_auth.dart';

import '../viewmodels/auth_view_model.dart';
import '../../services/driver_api.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen>
    with SingleTickerProviderStateMixin {
  final _driverApi = DriverApi();
  bool _uploadingPhoto = false;

  late final AnimationController _pulseController = AnimationController(
    vsync: this,
    duration: const Duration(seconds: 2),
  )..repeat(reverse: true);

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  Future<void> _pickAndUploadPhoto() async {
    final uid = FirebaseAuth.instance.currentUser?.uid;
    if (uid == null) return;

    final picked = await ImagePicker().pickImage(
      source: ImageSource.gallery,
      maxWidth: 1080,
      imageQuality: 85,
    );
    if (picked == null) return;

    setState(() => _uploadingPhoto = true);
    try {
      final ref = FirebaseStorage.instance.ref(
        'driver_avatars/$uid/${DateTime.now().millisecondsSinceEpoch}_${picked.name}',
      );
      await ref.putFile(File(picked.path));
      final url = await ref.getDownloadURL();
      await _driverApi.updatePhoto(uid, url);
      if (!mounted) return;
      await context.read<AuthViewModel>().refreshAccount(force: true);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Không tải được ảnh: $e')));
    } finally {
      if (mounted) setState(() => _uploadingPhoto = false);
    }
  }

  // Hàm hiển thị Dialog chung với hiệu ứng mượt mà (Scale & Fade)
  void _showAnimatedDialog({
    required BuildContext context,
    required String title,
    required Widget content,
    required List<Widget> actions,
  }) {
    showGeneralDialog(
      context: context,
      barrierDismissible: true,
      barrierLabel: 'Dismiss',
      transitionDuration: const Duration(milliseconds: 250),
      pageBuilder: (context, animation, secondaryAnimation) =>
          const SizedBox.shrink(),
      transitionBuilder: (context, animation, secondaryAnimation, child) {
        final curvedAnimation = CurvedAnimation(
          parent: animation,
          curve: Curves.easeOutBack,
        );

        return ScaleTransition(
          scale: curvedAnimation,
          child: FadeTransition(
            opacity: animation,
            child: AlertDialog(
              backgroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(24),
              ),
              title: Text(
                title,
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 18,
                ),
              ),
              content: content,
              actions: actions,
            ),
          ),
        );
      },
    );
  }

  // --- CHỈNH SỬA THÔNG TIN ---
  void _showEditProfileDialog(BuildContext context) {
    final account = context.read<AuthViewModel>().account;
    if (account == null) return;

    final nameController = TextEditingController(text: account.name);
    final phoneController = TextEditingController(text: account.phone);
    final licenseController = TextEditingController(
      text: account.licenseNumber,
    );
    bool isLoading = false;

    _showAnimatedDialog(
      context: context,
      title: 'Chỉnh sửa thông tin',
      content: StatefulBuilder(
        builder: (context, setStateDialog) => SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameController,
                decoration: const InputDecoration(
                  labelText: 'Họ và tên',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: phoneController,
                keyboardType: TextInputType.phone,
                decoration: const InputDecoration(
                  labelText: 'Số điện thoại',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: licenseController,
                decoration: const InputDecoration(
                  labelText: 'Số bằng lái',
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
        ),
      ),
      actions: [
        StatefulBuilder(
          builder: (context, setStateAction) => Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              TextButton(
                onPressed: isLoading ? null : () => Navigator.pop(context),
                child: const Text('Huỷ', style: TextStyle(color: Colors.grey)),
              ),
              const SizedBox(width: 8),
              Container(
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF2A8B88), Color(0xFF175452)],
                  ),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: FilledButton(
                  style: FilledButton.styleFrom(
                    backgroundColor: Colors.transparent,
                    shadowColor: Colors.transparent,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  onPressed: isLoading
                      ? null
                      : () async {
                          setStateAction(() => isLoading = true);
                          try {
                            final uid = FirebaseAuth.instance.currentUser?.uid;
                            if (uid != null) {
                              await _driverApi.updateDriverProfile(
                                uid,
                                nameController.text.trim(),
                                phoneController.text.trim(),
                                licenseController.text.trim(),
                              );
                              if (!context.mounted) return;
                              await context
                                  .read<AuthViewModel>()
                                  .refreshAccount(force: true);
                              if (!context.mounted) return;
                              Navigator.pop(context);
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text(
                                    'Cập nhật thông tin thành công!',
                                  ),
                                ),
                              );
                            }
                          } catch (e) {
                            setStateAction(() => isLoading = false);
                            if (!context.mounted) return;
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('Lỗi cập nhật: $e')),
                            );
                          }
                        },
                  child: isLoading
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(
                            color: Colors.white,
                            strokeWidth: 2,
                          ),
                        )
                      : const Text('Lưu thay đổi'),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // --- ĐỔI MẬT KHẨU ---
  void _showChangePasswordDialog(BuildContext context) {
    final newPasswordController = TextEditingController();
    bool isLoading = false;

    _showAnimatedDialog(
      context: context,
      title: 'Đổi mật khẩu',
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(
            controller: newPasswordController,
            obscureText: true,
            decoration: const InputDecoration(
              labelText: 'Mật khẩu mới (tối thiểu 6 ký tự)',
              border: OutlineInputBorder(),
            ),
          ),
        ],
      ),
      actions: [
        StatefulBuilder(
          builder: (context, setStateAction) => Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              TextButton(
                onPressed: isLoading ? null : () => Navigator.pop(context),
                child: const Text('Huỷ', style: TextStyle(color: Colors.grey)),
              ),
              const SizedBox(width: 8),
              Container(
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF2A8B88), Color(0xFF175452)],
                  ),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: FilledButton(
                  style: FilledButton.styleFrom(
                    backgroundColor: Colors.transparent,
                    shadowColor: Colors.transparent,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  onPressed: isLoading
                      ? null
                      : () async {
                          if (newPasswordController.text.length < 6) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text(
                                  'Mật khẩu phải có ít nhất 6 ký tự',
                                ),
                              ),
                            );
                            return;
                          }
                          setStateAction(() => isLoading = true);
                          try {
                            final user = FirebaseAuth.instance.currentUser;
                            await user?.updatePassword(
                              newPasswordController.text.trim(),
                            );
                            if (!context.mounted) return;
                            Navigator.pop(context);
                            if (!context.mounted) return;
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('Đổi mật khẩu thành công!'),
                              ),
                            );
                          } catch (e) {
                            setStateAction(() => isLoading = false);
                            if (!context.mounted) return;
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: Text(
                                  'Lỗi: Cần đăng nhập lại để đổi mật khẩu ($e)',
                                ),
                              ),
                            );
                          }
                        },
                  child: isLoading
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(
                            color: Colors.white,
                            strokeWidth: 2,
                          ),
                        )
                      : const Text('Xác nhận'),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // --- QUYỀN RIÊNG TƯ & BẢO MẬT ---
  void _showPrivacyDialog(BuildContext context) {
    _showAnimatedDialog(
      context: context,
      title: 'Quyền riêng tư & Bảo mật',
      content: const SingleChildScrollView(
        child: Text(
          '• Luồng video giám sát buồn ngủ được xử lý trực tiếp trên thiết bị (Edge AI) và chỉ trích xuất video ngắn 10 giây khi phát hiện sự cố để gửi về hệ thống quản trị.\n\n'
          '• Dữ liệu vị trí hành trình được mã hóa và chỉ phục vụ mục đích điều phối an toàn giao thông.\n\n'
          '• Mọi thông tin cá nhân và bằng lái của tài xế được bảo mật tuyệt đối theo quy định.',
          style: TextStyle(color: Colors.black87, height: 1.4),
        ),
      ),
      actions: [
        Container(
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF2A8B88), Color(0xFF175452)],
            ),
            borderRadius: BorderRadius.circular(12),
          ),
          child: FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: Colors.transparent,
              shadowColor: Colors.transparent,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            onPressed: () => Navigator.pop(context),
            child: const Text('Đã hiểu'),
          ),
        ),
      ],
    );
  }

  // --- CÀI ĐẶT ỨNG DỤNG ---
  void _showSettingsDialog(BuildContext context) {
    bool soundAlert = true;
    bool fcmNotification = true;

    _showAnimatedDialog(
      context: context,
      title: 'Cài đặt ứng dụng',
      content: StatefulBuilder(
        builder: (context, setStateDialog) => Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            SwitchListTile(
              title: const Text(
                'Âm thanh cảnh báo buồn ngủ',
                style: TextStyle(fontSize: 14),
              ),
              value: soundAlert,
              activeThumbColor: const Color(0xFF2A8B88),
              onChanged: (val) => setStateDialog(() => soundAlert = val),
            ),
            SwitchListTile(
              title: const Text(
                'Nhận thông báo đẩy (FCM)',
                style: TextStyle(fontSize: 14),
              ),
              value: fcmNotification,
              activeThumbColor: const Color(0xFF2A8B88),
              onChanged: (val) => setStateDialog(() => fcmNotification = val),
            ),
            const Divider(),
            const ListTile(
              dense: true,
              title: Text(
                'Phiên bản ứng dụng',
                style: TextStyle(color: Colors.grey),
              ),
              trailing: Text(
                'v1.0.0 (Graduation Thesis)',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
            ),
          ],
        ),
      ),
      actions: [
        Container(
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF2A8B88), Color(0xFF175452)],
            ),
            borderRadius: BorderRadius.circular(12),
          ),
          child: FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: Colors.transparent,
              shadowColor: Colors.transparent,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            onPressed: () => Navigator.pop(context),
            child: const Text('Đóng'),
          ),
        ),
      ],
    );
  }

  // --- TRỢ GIÚP & HỖ TRỢ ---
  void _showHelpDialog(BuildContext context) {
    _showAnimatedDialog(
      context: context,
      title: 'Trợ giúp & Hỗ trợ',
      content: const Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Nếu bạn gặp sự cố kỹ thuật hoặc cần hỗ trợ tài khoản, vui lòng liên hệ ban quản trị đồ án:',
            style: TextStyle(height: 1.4),
          ),
          SizedBox(height: 12),
          Text(
            '• Hotline: 1900 xxxx (24/7)',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          SizedBox(height: 4),
          Text(
            '• Email: support@drivermonitoring.vn',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
        ],
      ),
      actions: [
        Container(
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF2A8B88), Color(0xFF175452)],
            ),
            borderRadius: BorderRadius.circular(12),
          ),
          child: FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: Colors.transparent,
              shadowColor: Colors.transparent,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            onPressed: () => Navigator.pop(context),
            child: const Text('Đóng'),
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final account = context.watch<AuthViewModel>().account;
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 105, 16, 120),
        children: [
          FadeInDown(
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(24),
                border: Border.all(
                  color: Colors.white.withValues(alpha: 0.9),
                  width: 1.5,
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.04),
                    blurRadius: 16,
                    offset: const Offset(0, 6),
                  ),
                  BoxShadow(
                    color: const Color(0xFF2A8B88).withValues(alpha: 0.08),
                    blurRadius: 24,
                    offset: const Offset(0, 10),
                  ),
                ],
              ),
              child: Row(
                children: [
                  Stack(
                    alignment: Alignment.bottomRight,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(2),
                        decoration: const BoxDecoration(
                          shape: BoxShape.circle,
                          gradient: LinearGradient(
                            colors: [Color(0xFF2A8B88), Color(0xFF175452)],
                          ),
                        ),
                        child: CircleAvatar(
                          radius: 32,
                          backgroundColor: Colors.white,
                          backgroundImage: NetworkImage(
                            account?.photoUrl ??
                                'https://cdn-icons-png.flaticon.com/512/3135/3135715.png',
                          ),
                        ),
                      ),
                      Material(
                        color: const Color(0xFF2A8B88),
                        shape: const CircleBorder(),
                        elevation: 2,
                        child: InkWell(
                          customBorder: const CircleBorder(),
                          onTap: _uploadingPhoto ? null : _pickAndUploadPhoto,
                          child: Padding(
                            padding: const EdgeInsets.all(4),
                            child: _uploadingPhoto
                                ? const SizedBox(
                                    width: 12,
                                    height: 12,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      color: Colors.white,
                                    ),
                                  )
                                : const Icon(
                                    FluentIcons.camera_24_regular,
                                    color: Colors.white,
                                    size: 14,
                                  ),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                account?.name ?? 'Tài xế',
                                style: const TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.black87,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            AnimatedBuilder(
                              animation: _pulseController,
                              builder: (context, child) {
                                return Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 8,
                                    vertical: 4,
                                  ),
                                  decoration: BoxDecoration(
                                    color: Colors.green.withValues(
                                      alpha:
                                          0.1 + (_pulseController.value * 0.15),
                                    ),
                                    borderRadius: BorderRadius.circular(12),
                                    border: Border.all(
                                      color: Colors.green.withValues(
                                        alpha: 0.4,
                                      ),
                                    ),
                                  ),
                                  child: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Container(
                                        width: 6,
                                        height: 6,
                                        decoration: BoxDecoration(
                                          shape: BoxShape.circle,
                                          color: Colors.green.withValues(
                                            alpha:
                                                0.5 +
                                                (_pulseController.value * 0.5),
                                          ),
                                        ),
                                      ),
                                      const SizedBox(width: 4),
                                      const Text(
                                        'Online',
                                        style: TextStyle(
                                          fontSize: 10,
                                          fontWeight: FontWeight.bold,
                                          color: Colors.green,
                                        ),
                                      ),
                                    ],
                                  ),
                                );
                              },
                            ),
                          ],
                        ),
                        const SizedBox(height: 6),
                        Text(
                          [
                            account?.phone,
                            account?.licenseNumber,
                          ].where((s) => s != null && s.isNotEmpty).join(' • '),
                          style: TextStyle(
                            fontSize: 13,
                            color: Colors.grey.shade600,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 20),

          FadeInUp(
            delay: const Duration(milliseconds: 100),
            child: _buildSectionGroup(
              title: 'Tài khoản',
              children: [
                _buildListTile(
                  icon: FluentIcons.person_24_regular,
                  title: 'Chỉnh sửa thông tin',
                  onTap: () => _showEditProfileDialog(context),
                ),
                _buildListTile(
                  icon: FluentIcons.key_24_regular,
                  title: 'Đổi mật khẩu',
                  onTap: () => _showChangePasswordDialog(context),
                ),
                _buildListTile(
                  icon: FluentIcons.shield_checkmark_24_regular,
                  title: 'Quyền riêng tư & Bảo mật',
                  onTap: () => _showPrivacyDialog(context),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          FadeInUp(
            delay: const Duration(milliseconds: 200),
            child: _buildSectionGroup(
              title: 'Hệ thống',
              children: [
                _buildListTile(
                  icon: FluentIcons.settings_24_regular,
                  title: 'Cài đặt ứng dụng',
                  onTap: () => _showSettingsDialog(context),
                ),
                _buildListTile(
                  icon: FluentIcons.question_circle_24_regular,
                  title: 'Trợ giúp & Hỗ trợ',
                  onTap: () => _showHelpDialog(context),
                ),
                _buildListTile(
                  icon: FluentIcons.sign_out_24_regular,
                  title: 'Đăng xuất',
                  titleColor: Colors.redAccent,
                  iconColor: Colors.redAccent,
                  hideArrow: true,
                  onTap: () => context.read<AuthViewModel>().signOut(),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionGroup({
    required String title,
    required List<Widget> children,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 12, bottom: 6),
          child: Text(
            title.toUpperCase(),
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: Colors.grey.shade500,
              letterSpacing: 0.8,
            ),
          ),
        ),
        Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: Colors.white.withValues(alpha: 0.8),
              width: 1.5,
            ),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.03),
                blurRadius: 12,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Column(children: children),
        ),
      ],
    );
  }

  Widget _buildListTile({
    required IconData icon,
    required String title,
    required VoidCallback onTap,
    Color? iconColor,
    Color? titleColor,
    bool hideArrow = false,
  }) {
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      leading: Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: (iconColor ?? const Color(0xFF2A8B88)).withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Icon(
          icon,
          color: iconColor ?? const Color(0xFF2A8B88),
          size: 22,
        ),
      ),
      title: Text(
        title,
        style: TextStyle(
          fontWeight: FontWeight.w600,
          color: titleColor ?? Colors.black87,
          fontSize: 15,
        ),
      ),
      trailing: hideArrow
          ? null
          : Icon(
              FluentIcons.ios_arrow_rtl_24_regular,
              color: Colors.grey.shade400,
              size: 20,
            ),
      onTap: onTap,
    );
  }
}
