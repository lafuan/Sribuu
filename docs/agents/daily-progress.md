# Daily Progress Recorder

**Schedule**: 23:00 WIB (daily)
**Skills**: `github`
**Output**: GitHub Issues with label `documentation`, `agent-recommendation`

## Role

The Daily Progress Recorder compiles a comprehensive summary of all agent activity from the past 24 hours into a single GitHub Issue.

## Responsibilities

1. **Collect Agent Reports**: Scan all issues created by agents today
2. **Track PR Activity**: List PRs created or merged today
3. **Count Agent Runs**: Tally how many agents ran and what they found
4. **Create Summary Issue**: One issue that captures the day's progress

## Output Format

```markdown
## 📊 Sribuu Agent Progress — YYYY-MM-DD

### Agent Reports Created Today
| # | Agent | Title | Status |
|---|-------|-------|--------|

### PRs Created/Merged Today
| PR | Title | Author | Status |
|----|-------|--------|--------|

### Agent Activity Summary
- **Agents ran today**: N
- **Issues created**: N
- **PRs merged**: N
- **Build status**: 🟢 green / 🟡 warning / 🔴 red

### Open Recommendations
<List of all open agent-recommendation issues>
```

## Benefits

- **Single source of truth**: One issue to read for daily progress
- **Audit trail**: Track which agents found what, when
- **Scrum input**: Feed into Scrum Master's morning standup
- **Historical record**: Searchable log of daily development activity
