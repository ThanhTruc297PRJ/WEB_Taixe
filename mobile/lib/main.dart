import 'package:flutter/material.dart';
import 'package:flutter_foreground_task/flutter_foreground_task.dart';
import 'package:provider/provider.dart';

import 'presentation/screens/monitoring_screen.dart';
import 'presentation/viewmodels/monitoring_view_model.dart';

void main() {
  // Cần gọi trước runApp để nhận dữ liệu từ MonitoringTaskHandler.
  FlutterForegroundTask.initCommunicationPort();
  runApp(const DriverSafetyApp());
}

class DriverSafetyApp extends StatelessWidget {
  const DriverSafetyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => MonitoringViewModel(),
      child: MaterialApp(
        title: 'Driver Safety Monitoring',
        theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple)),
        home: const MonitoringScreen(),
      ),
    );
  }
}
