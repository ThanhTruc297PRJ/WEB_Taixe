import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:apphotrotaixe/main.dart';

ElevatedButton _buttonWithText(WidgetTester tester, String text) {
  final finder = find.ancestor(
    of: find.text(text),
    matching: find.byWidgetPredicate((widget) => widget is ElevatedButton),
  );
  return tester.widget<ElevatedButton>(finder);
}

void main() {
  testWidgets('RadioTestPage renders in stopped state', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(const MyApp());

    expect(find.text('Test Radio Stream'), findsOneWidget);
    expect(find.text('Đã dừng'), findsOneWidget);
  });

  testWidgets('Pause and Stop are disabled before playback starts', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(const MyApp());

    expect(_buttonWithText(tester, 'Pause').onPressed, isNull);
    expect(_buttonWithText(tester, 'Stop').onPressed, isNull);
    expect(_buttonWithText(tester, 'Play').onPressed, isNotNull);
  });
}
