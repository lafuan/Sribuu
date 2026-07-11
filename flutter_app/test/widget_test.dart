import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:sribuu_app/main.dart';

void main() {
  testWidgets('SribuuApp renders without crashing', (WidgetTester tester) async {
    await tester.pumpWidget(const SribuuApp());

    // The app should render SribuuWebView
    expect(find.byType(SribuuWebView), findsOneWidget);
  });

  testWidgets('SribuuApp has correct title', (WidgetTester tester) async {
    await tester.pumpWidget(const SribuuApp());

    // AppBar title should be 'Sribuu'
    expect(find.text('Sribuu'), findsOneWidget);
  });

  testWidgets('SribuuApp shows loading indicator on startup', (WidgetTester tester) async {
    await tester.pumpWidget(const SribuuApp());

    // Initially the loading progress bar should be visible
    expect(find.byType(LinearProgressIndicator), findsOneWidget);
  });
}
