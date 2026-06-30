# Mobile Agent

**Schedule**: 06:00, 18:00 WIB (2x daily)
**Skills**: `flutter-mobile-app`, `clean-code`
**Output**: GitHub Issues with label `mobile`, `agent-recommendation`

## Role

The Mobile Agent audits the Flutter iOS app for code quality, build health, and best practices.

## Audit Dimensions

### 1. Flutter Code Quality
- `flutter analyze` output: lint warnings and errors
- Large widget files (>400 lines) needing extraction
- Unused imports and dead code
- State management patterns (setState vs Provider/Riverpod)

### 2. iOS Build Health
- `flutter build ipa` success/failure rate over recent runs
- Build output size trends
- `Podfile` and dependency freshness
- Xcode project configuration consistency

### 3. Platform Code
- Swift/Kotlin native code in `ios/` or `android/` folders
- Plugin versions and compatibility
- iOS Info.plist required keys (camera, location permissions if any)

### 4. Dependency Audit
- `pub outdated`: packages behind latest version
- Transitive dependency conflicts
- Direct dependencies with security advisories
- Unused dependencies in `pubspec.yaml`

### 5. Asset Management
- Missing asset declarations in `pubspec.yaml`
- Large assets (>500KB) that should be optimized
- Duplicate or unused assets

## Tech Stack Context

| Component | Technology |
|-----------|-----------|
| Framework | Flutter 3.27.4 |
| Target | iOS (unsigned IPA for sideloading) |
| State management | TBD |
| Build system | GitHub Actions (macos-latest) |
| Output | Unsigned .ipa via manual Payload/ packaging |

## Common Issues Flagged

| Issue | Severity |
|-------|----------|
| Flutter analyze errors | High |
| Widget >500 lines | Medium |
| 10+ outdated packages | Medium |
| Build failure in CI | Critical |
| Missing `pubspec.yaml` asset entry | Medium |
| Large unoptimized assets | Low |
