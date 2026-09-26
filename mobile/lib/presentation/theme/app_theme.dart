import 'package:flutter/material.dart';

class AppTheme {
  // Màu sắc chủ đạo Automotive Teal Gradient
  static const Color primaryTeal = Color(0xFF2A8B88);
  static const Color darkTeal = Color(0xFF175452);
  static const Color lightBg = Color(0xFFF9FAFB);

  // Gradient chuẩn cho nút bấm và card nổi bật
  static const LinearGradient primaryGradient = LinearGradient(
    colors: [Color(0xFF2A8B88), Color(0xFF175452)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  // Hiệu ứng đổ bóng đa tầng kết hợp viền sáng kính mờ
  static List<BoxShadow> cardShadow = [
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
  ];

  static Border cardBorder = Border.all(
    color: Colors.white.withValues(alpha: 0.8),
    width: 1.5,
  );
}
