# Frontend Agent

**Schedule**: 12:00, 18:00, 00:00 WIB (3x daily)
**Skills**: `ux-heuristics`, `refactoring-ui`, `ios-hig-design`, `web-typography`, `microinteractions`
**Output**: GitHub Issues with label `frontend`, `agent-recommendation`

## Role

The Frontend Agent audits the Jinja2 + HTMX + Tailwind frontend for UI inconsistencies, accessibility issues, and performance problems.

## Audit Dimensions

### 1. HTML/CSS Quality
- **Inline styles**: Should use Tailwind utility classes instead
- **Image alt text**: Every `<img>` must have descriptive `alt` attribute
- **Duplicate styles**: Repeated CSS across templates
- **CDN usage**: Redundant Tailwind CDN if output.css is already built

### 2. Accessibility
- **Heading hierarchy**: Proper H1→H6 nesting (no skipped levels)
- **Color contrast**: Minimum WCAG AA compliance
- **Keyboard navigation**: All interactive elements reachable via Tab
- **ARIA labels**: Interactive controls have accessible names

### 3. HTMX Best Practices
- **Loading indicators**: Every `hx-get`/`hx-post` should have `hx-indicator`
- **Error handling**: `hx-target-error` for failed requests
- **Progressive enhancement**: Works without JavaScript where possible

### 4. Template Health
- **File sizes**: Templates over 300 lines may need component extraction
- **Component reuse**: Nav, footer, sidebar should be in `components/` folder
- **Inheritance**: Check consistent use of `base.html` blocks

## Tech Stack Context

- **Templates**: Jinja2 with `base.html` inheritance
- **Interactivity**: HTMX (no heavy JS framework)
- **CSS**: Tailwind CSS (via standalone CLI build)
- **Charts**: D3.js for visualization

## Common Issues Flagged

| Issue | Pattern | Severity |
|-------|---------|----------|
| Inline `style=""` | Bypasses Tailwind, hard to maintain | Medium |
| Missing `alt` on `<img>` | Accessibility violation | High |
| No `hx-indicator` | No loading state feedback | Medium |
| `<h3>` skipping `<h2>` | Broken heading structure | High |
| Duplicate CDN + local CSS | Redundant 500KB load | Medium |

## Recent Activity

### 2026-07-03
- Issue [#204](https://github.com/lafuan/Sribuu/issues/204): Frontend Audit: Inline styles stuck at 27, modals missing ARIA, HTMX loading gap persists — ⏳ OPEN

### 2026-07-01
- Issue [#164](https://github.com/lafuan/Sribuu/issues/164): [Frontend Agent] Heading hierarchy violations (missing H1s, duplicate H1s) + unpurged Tailwind CSS — ⏳ OPEN
- Issue [#163](https://github.com/lafuan/Sribuu/issues/163): [Frontend Agent] Heading hierarchy violations (missing H1s, duplicate H1s) + unpurged Tailwind CSS — ✅ CLOSED

### 2026-06-30
- Issue [#120](https://github.com/lafuan/Sribuu/issues/120): [Frontend Agent] Remove redundant CDN Tailwind + Move inline style to input.css — ✅ CLOSED
- Issue [#121](https://github.com/lafuan/Sribuu/issues/121): [Frontend Agent] Clean up inline styles (27x) + Audit accessibility — ⏳ OPEN
