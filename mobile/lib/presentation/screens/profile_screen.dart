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

class _ProfileScreenState extends State<ProfileScreen> {
  final _driverApi = DriverApi();
  bool _uploadingPhoto = false;

  /// Chọn ảnh từ thư viện -> upload lên Firebase Storage (client-side, giống
  /// cách web admin đang làm cho tài khoản admin) -> lưu URL vào hồ sơ qua
  /// backend -> nạp lại hồ sơ để hiện ảnh mới ngay.
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
      if (mounted) {
        await context.read<AuthViewModel>().refreshAccount(force: true);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Không tải được ảnh: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _uploadingPhoto = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final account = context.watch<AuthViewModel>().account;
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFFFFF0F0), Colors.white],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            FadeInDown(
              child: Center(
                child: Column(
                  children: [
                    Stack(
                      alignment: Alignment.bottomRight,
                      children: [
                        Container(
                          padding: const EdgeInsets.all(4),
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: const Color(0xFFD32F2F),
                              width: 2,
                            ),
                          ),
                          child: CircleAvatar(
                            radius: 50,
                            backgroundColor: Colors.white,
                            backgroundImage: NetworkImage(
                              account?.photoUrl ??
                                  'https://cdn-icons-png.flaticon.com/512/3135/3135715.png',
                            ),
                          ),
                        ),
                        Material(
                          color: const Color(0xFFD32F2F),
                          shape: const CircleBorder(),
                          child: InkWell(
                            customBorder: const CircleBorder(),
                            onTap: _uploadingPhoto ? null : _pickAndUploadPhoto,
                            child: Padding(
                              padding: const EdgeInsets.all(6),
                              child: _uploadingPhoto
                                  ? const SizedBox(
                                      width: 16,
                                      height: 16,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                        color: Colors.white,
                                      ),
                                    )
                                  : const Icon(
                                      FluentIcons.camera_24_regular,
                                      color: Colors.white,
                                      size: 16,
                                    ),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Text(
                      account?.name ?? 'Tài xế',
                      style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      [account?.phone, account?.licenseNumber]
                          .where((s) => s != null && s.isNotEmpty)
                          .join(' • '),
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey.shade600,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 30),

            FadeInUp(
              delay: const Duration(milliseconds: 100),
              child: _buildSectionGroup(
                title: 'Tài khoản',
                children: [
                  _buildListTile(
                    icon: FluentIcons.person_24_regular,
                    title: 'Chỉnh sửa thông tin',
                    onTap: () {},
                  ),
                  _buildListTile(
                    icon: FluentIcons.key_24_regular,
                    title: 'Đổi mật khẩu',
                    onTap: () {},
                  ),
                  _buildListTile(
                    icon: FluentIcons.shield_checkmark_24_regular,
                    title: 'Quyền riêng tư & Bảo mật',
                    onTap: () {},
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            FadeInUp(
              delay: const Duration(milliseconds: 200),
              child: _buildSectionGroup(
                title: 'Hệ thống',
                children: [
                  _buildListTile(
                    icon: FluentIcons.settings_24_regular,
                    title: 'Cài đặt ứng dụng',
                    onTap: () {},
                  ),
                  _buildListTile(
                    icon: FluentIcons.question_circle_24_regular,
                    title: 'Trợ giúp & Hỗ trợ',
                    onTap: () {},
                  ),
                  _buildListTile(
                    icon: FluentIcons.sign_out_24_regular,
                    title: 'Đăng xuất',
                    titleColor: Colors.red,
                    iconColor: Colors.red,
                    hideArrow: true,
                    onTap: () => context.read<AuthViewModel>().signOut(),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 80),
          ],
        ),
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
          padding: const EdgeInsets.only(left: 12, bottom: 8),
          child: Text(
            title.toUpperCase(),
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: Colors.grey.shade500,
            ),
          ),
        ),
        Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(20),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.03),
                blurRadius: 10,
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
      leading: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: (iconColor ?? Colors.black87).withOpacity(0.05),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Icon(icon, color: iconColor ?? Colors.black87, size: 22),
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
