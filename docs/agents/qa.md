# QA Agent

**Schedule**: Every 2 hours
**Skills**: `testing`, `systematic-debugging`, `web-app-qa`
**Output**: GitHub Issues with label `bug`, `agent-recommendation`

## Role

The QA Agent monitors CI pipeline health, detects flaky tests, and identifies testing coverage gaps.

## Audit Dimensions

### 1. CI Run Health
- Check last 5 workflow runs on `main` branch
- Track success/failure trends over time
- Alert on cascading failures (multiple runs failing in sequence)

### 2. Flaky Test Detection
- Scan failed run logs for test failures
- Identify tests that fail intermittently (passing on retry)
- Flag non-deterministic test patterns

### 3. Test Coverage
- Count test modules vs source modules
- Identify untested routes and services
- Check code coverage thresholds in CI config

### 4. E2E Test Status
- Count E2E test files
- Alert if zero E2E tests exist
- Recommend E2E test scenarios for critical flows

## Test Infrastructure

| Component | Tool |
|-----------|------|
| Unit/Integration | pytest + pytest-asyncio |
| Coverage | pytest-cov |
| E2E | Playwright |
| CI | GitHub Actions |

## Silencing Policy

If no CI failures and no coverage gaps are found, the QA Agent responds with `[SILENT]` to reduce noise.

## Common Issues Flagged

| Issue | Severity |
|-------|----------|
| 100+ tests broken | Critical |
| No E2E tests | Medium |
| Module without test file | Low |
| Stale PRs >24h | Warning |
| Coverage below 85% | Medium |
