# Mobile Agent — Flutter iOS App Audit & Update

**Schedule:** Daily 06:00, 18:00 WIB
**Model:** `ocg`
**Skills:** Flutter Mobile App, Clean Code

## Activity Log

| Date | Issues Created | PRs Merged | Build Status |
|------|----------------|------------|--------------|
| 2026-07-08 06:00 | #507, #508, #509, #510, #511, #512 | — | ❌ Deploy: FAIL — iOS build: N/A (workflow not on main) |
| 2026-07-08 18:00 | #589, #590, #591 | — | ❌ Deploy: FAIL — iOS build: N/A |
| 2026-07-09 06:00 | — | — | ❌ Deploy: FAIL — iOS build: N/A |
| 2026-07-09 18:00 | #675 (flutter_lints) | — | ❌ Deploy: FAIL — iOS build: N/A |
| 2026-07-10 06:00 | #722-#725 | — | ❌ Deploy: FAIL — iOS build: N/A |
| 2026-07-10 18:00 | — | — | ❌ Deploy: FAIL — iOS build: N/A |
| 2026-07-12 06:00 | #852, #853, #854, #855 | #729 (D1 fix), #785 (index fix) | ✅ Deploy: **GREEN** — iOS build: N/A (PR #816 open) |
| 2026-07-13 18:00 | #884, #885, #886 | — | ✅ Deploy: **GREEN** (2/2 runs) — iOS build: N/A (PR #816 open, behind main) |
| 2026-07-14 06:00 | #921, #922 | — | ✅ Deploy: **GREEN** (10+ consecutive) — iOS build: N/A (PR #816 open, behind main) |
| 2026-07-14 18:00 | #940, #941 | — | ✅ Deploy: **GREEN** (10+ consecutive) — iOS build: N/A (PR #816 open, 97 behind main) |
| 2026-07-17 23:00 | (issues saved as .md — gh CLI not auth'd) | — | ✅ Deploy: GREEN — iOS build: **🔴 BLOCKED (missing Podfile)** |

**Latest Run:** 2026-07-17 23:00 WIB

---

## Findings — 2026-07-17 23:00 WIB

### Status Overview

PR #816 (`fix/ios-url-wrong-backend-clean`) is **84 commits behind main** (consistent gap since Jul 14). Info.plist issues from #941 are **RESOLVED**. Three new findings documented below.

### 1. 🔴 HIGH: Missing `ios/Podfile` — iOS build will fail

**New finding.** `flutter_app/ios/Podfile` does not exist in the branch.

Without Podfile, `flutter pub get` cannot resolve CocoaPods native dependencies (webview_flutter's WKWebView pod). The `ios-build.yml` CI workflow step `flutter pub get` and subsequent `flutter build ipa` will fail.

**Issue file:** `.github/issues/d1-missing-ios-podfile.md`
**Fix:** Run `flutter create --platforms=ios .` from `flutter_app/` directory to regenerate Podfile.

### 2. ✅ RESOLVED: Info.plist (#941) — all three items fixed

Verified `flutter_app/ios/Runner/Info.plist`:

| Item | #941 complaint | Now | |
|------|----------------|-----|--|
| Display name | `Sribuu App` | `Sribuu` | ✅ |
| iPhone orientation | portrait + landscape | portrait-only | ✅ |
| NSAppTransportSecurity | missing | present with `NSAllowsArbitraryLoads` | ✅ |

**Issue file:** `.github/issues/d1-ios-info-plist-fixed.md`
**Note:** #854 (restrict NSAllowsArbitraryLoads to sribuu.pages.dev) still open.

### 3. 🟡 MEDIUM: Flutter CI version 3.27.4 behind latest stable 3.44.6

CI pins Flutter 3.27.4 (Dart 3.6). Flutter stable is **3.44.6** (Jul 8, 2026). Blocks all 3 dep upgrades:

| Package | Pinned | Latest | Required Dart |
|---------|--------|--------|---------------|
| `webview_flutter` | ^4.13.0 | 4.14.1 | 3.38+ |
| `cupertino_icons` | ^1.0.8 | 1.0.9 | 3.9+ |
| `flutter_lints` | ^5.0.0 | 6.0.0 | 3.8+ |

**Issue file:** `.github/issues/d1-flutter-ci-version-gap.md`

### 4. 🟡 MEDIUM: No offline/error state in WebView

`onWebResourceError` only `debugPrint`s — no user-facing UI. Device offline or backend down → blank white screen with no retry.

**Issue file:** `.github/issues/d1-ios-offline-error-handling.md`

### 5. 🟡 PR #816 gap: 84 commits behind main

| Metric | Jul 14 | Jul 17 |
|--------|:------:|:------:|
| Commits behind main | 97 | **84** (reduced — some rebasing?) |
| Risk | HIGH | MEDIUM — gap slightly closed but still substantial |

### 6. 🟢 AppDelegate.swift — standard boilerplate, no code issues

### Issues Created (as .md files — gh CLI not authenticated)

| File | Title | Severity |
|------|-------|----------|
| `d1-missing-ios-podfile.md` | Missing ios/Podfile — build blocker | 🔴 HIGH |
| `d1-ios-info-plist-fixed.md` | Info.plist #941 resolved | ✅ (info) |
| `d1-flutter-ci-version-gap.md` | Flutter 3.27.4 → 3.44.6 needed | 🟡 MEDIUM |
| `d1-ios-offline-error-handling.md` | No offline error screen in WebView | 🟡 MEDIUM |

## Open PRs Summary

| PR | Branch | Base | State | Blocked By |
|----|--------|------|-------|------------|
| **#816** | fix/ios-url-wrong-backend-clean | main | **OPEN (84 BEHIND MAIN)** | needs merge urgently |
| #388 | fix/384-d1-migration-idempotent | main | OPEN (CONFLICTING) | should close — #922 opened |

## Critical Blockers (priority order)

1. **(NEW) 🔴 Fix missing Podfile** — without it, iOS build cannot proceed. Must fix before PR #816 merge.
2. **🔴 Merge PR #816** — 84 commits behind, gap persistent. Needs urgent merge.
3. **🟡 Fix offline error handling** — improves UX, prevents blank screen on network issues.
4. **🟡 Bump Flutter CI 3.27.4 → 3.44.6** — unblocks all dep upgrades.
5. **🟢 Info.plist #941 issues** — RESOLVED. Close #941.
6. **🟢 Close PR #388** (#922) — conflicting, superseded.
