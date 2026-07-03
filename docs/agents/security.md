# Security Agent

**Schedule**: 03:00, 09:00, 15:00, 21:00 WIB (4x daily)
**Skills**: `release-it`, `clean-code`, `software-design-philosophy`
**Output**: GitHub Issues with label `security`, `agent-recommendation`

## Role

The Security Agent performs comprehensive security auditing across five dimensions: code, infrastructure, CI/CD, dependencies, and environment.

## Audit Dimensions

### 1. Code Security (SAST)
- **Bandit static analysis**: HIGH/MEDIUM severity findings in `backend/` folder
- **Hardcoded secrets**: API keys, passwords, tokens in source code
- **Dangerous functions**: `eval()`, `exec()`, `os.system()` calls
- **SQL injection**: f-string query construction without parameterization
- **File upload safety**: Unsanitized paths, missing type validation

### 2. Infrastructure Security
- **SSH hardening**: Root login disabled, key-only authentication, non-default port
- **Open ports**: Only 80, 443, 22 (or alt SSH port)
- **Firewall**: UFW active with default-deny inbound policy
- **Fail2ban**: Active and configured for SSH, nginx, app
- **World-writable files**: `find / -perm -002` in sensitive directories
- **Unused users**: Stale system accounts with shell access

### 3. CI/CD Workflow Security
- **GitHub Actions permissions**: `contents: write` scope — is it necessary?
- **Risky triggers**: `pull_request_target` (runs in base repo context)
- **Branch protection**: Rules on `main` branch
- **Secret scanning**: GitHub secret scanning alerts
- **Dependabot**: Enabled and active

### 4. Dependency Security
- **pip-audit**: Python packages with known CVEs
- **npm audit**: Frontend dependencies (if any)
- **Outdated packages**: Critical/security-related packages behind latest
- **Dependabot PRs**: Stale security patches not merged

### 5. Environment Security
- **.env in git**: Check `.gitignore` coverage
- **Sensitive file permissions**: 600 on `.env`, private keys
- **Debug mode**: `DEBUG=True` in production
- **CORS**: Overly permissive origins

## Severity Classification

| Finding | Severity |
|---------|----------|
| Production exploit (SQL injection, RCE) | 🔴 Critical |
| Sensitive credentials exposed | 🔴 Critical |
| CVE in dependency with public exploit | 🔴 Critical |
| Missing firewall / root SSH | 🟠 High |
| CVE in dependency without public exploit | 🟡 Medium |
| Debug mode in staging | 🟡 Medium |
| Missing .gitignore entry | 🟢 Low |
| Optional hardening (fail2ban) | 🟢 Low |

## Output Behavior

- **CRITICAL**: Create GitHub Issue immediately
- **HIGH**: Include in report with recommendation
- **MEDIUM/LOW**: List in summary only
- **Clean**: "✅ Security audit clean — no findings"

## Recent Activity

### 2026-07-03
- Issue [#205](https://github.com/lafuan/Sribuu/issues/205): [Agent] Security Audit: UFW inactive & PasswordAuthentication enabled on VPS — ⏳ OPEN

### 2026-07-02
- Issue [#183](https://github.com/lafuan/Sribuu/issues/183): CRITICAL: Security gaps — password SSH auth enabled, no firewall — ⏳ OPEN

### 2026-06-30
- Issue [#124](https://github.com/lafuan/Sribuu/issues/124): [Security Agent] 🚨 CRITICAL: Database password exposed in plaintext in deploy.yml — ⏳ OPEN
- Issue [#125](https://github.com/lafuan/Sribuu/issues/125): [Security Agent] 🔴 HIGH: SSH PasswordAuth enabled + No firewall/IDS on production VPS — ⏳ OPEN
- Issue [#126](https://github.com/lafuan/Sribuu/issues/126): [Security Agent] 🔴 HIGH: deploy.yml & ios-build.yml missing explicit permissions — ⏳ OPEN
- Issue [#127](https://github.com/lafuan/Sribuu/issues/127): [Security Agent] 🔴 HIGH: deploy.yml & ios-build.yml missing explicit permissions — ✅ CLOSED
- Issue [#129](https://github.com/lafuan/Sribuu/issues/129): ⚠️ Security hardening: UFW firewall not active + SSH password auth enabled — ⏳ OPEN
- Issue [#130](https://github.com/lafuan/Sribuu/issues/130): [Security Agent] 🟡 MEDIUM: __import__() usage in rule_service.py + missing .gitignore patterns — ⏳ OPEN
- Issue [#140](https://github.com/lafuan/Sribuu/issues/140): 🔴 CRITICAL: VPS Security Gaps Detected — UFW Inactive, Password Auth Enabled — ⏳ OPEN
