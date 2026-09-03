import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class MaintenanceViewModel extends ChangeNotifier {
  DateTime? inspectionDate;
  DateTime? oilChangeDate;

  MaintenanceViewModel() {
    _loadDates();
  }

  Future<void> _loadDates() async {
    final prefs = await SharedPreferences.getInstance();
    final inspectionStr = prefs.getString('inspection_date');
    final oilChangeStr = prefs.getString('oil_change_date');

    if (inspectionStr != null) inspectionDate = DateTime.parse(inspectionStr);
    if (oilChangeStr != null) oilChangeDate = DateTime.parse(oilChangeStr);
    notifyListeners();
  }

  Future<void> saveInspectionDate(DateTime date) async {
    inspectionDate = date;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('inspection_date', date.toIso8601String());
    notifyListeners();
  }

  Future<void> saveOilChangeDate(DateTime date) async {
    oilChangeDate = date;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('oil_change_date', date.toIso8601String());
    notifyListeners();
  }

  int get daysUntilInspection {
    if (inspectionDate == null) return 0;
    return inspectionDate!.difference(DateTime.now()).inDays;
  }

  int get daysUntilOilChange {
    if (oilChangeDate == null) return 0;
    return oilChangeDate!.difference(DateTime.now()).inDays;
  }
}
