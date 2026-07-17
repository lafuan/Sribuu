---
version: alpha
name: Sribuu (Finance) — Y2K Console Chrome Adaptation
description: Sribuu personal finance tracker redesigned with Nintendo 2001's beveled-metal-plate aesthetic, adapted for a dark green/teal financial tool. Every panel is a chamfered metal plate, nav bars carry halftone dot texture, and warm amber signals every action.
---

# Sribuu Design Token — Y2K Console Chrome (Finance)

## Brand Adaptation
The Nintendo 2001 design language translated for a **personal finance tracker**:
- **Periwinkle chrome → Dark teal/emerald chassis** (#0d2818 canvas, #115e59 raised panels) — a cool green "money" foundation
- **Nintendo red → Emerald green** (#059669) as the brand anchor for primary actions
- **Carbon navy preserved** (#020617) — nav bars, footer, command layer
- **Amber/signal preserved** — amber for utility buttons, signal green for forward/submit actions
- **Halftone dot texture** on carbon bars — retained as the Y2K signature
- **Beveled edges** with bright top highlight and chrome-teal (#0d9488) shadow beneath

## Colors

# brand & accent
--sribuu-primary: #059669        # Emerald 600 — brand green, primary actions
--sribuu-signal: #10b981         # Emerald 400 — forward action, submit
--sribuu-amber: #d97706          # Amber 600 — utility buttons, badges
--sribuu-nav-gold: #f59e0b       # Amber 500 — nav link glow

# surface chrome (cool green metallic)
--sribuu-canvas: #0d2818         # Dark green metallic — primary interface body
--sribuu-canvas-soft: #1a3a2a    # Pale teal — secondary-nav strip, inset panels
--sribuu-lavender: #064e3b       # Dark emerald — hero/balance fields
--sribuu-ice: #0f766e            # Teal — secondary hero panels
--sribuu-periwinkle: #115e59     # Raised mid panels
--sribuu-chrome-indigo: #0d9488  # Bevel borders, tab edges (teal chrome)
--sribuu-muted-indigo: #0f766e   # Inactive tabs, recessed chrome
--sribuu-platinum: #1e293b       # Slate 800 — list rows, inset surfaces
--sribuu-surface: #1e293b        # Content cards, form fields
--sribuu-carbon: #020617         # Slate 950 — nav bar, dark buttons, footer
--sribuu-hairline: #334155       # Slate 700 — bevel dividers
--sribuu-ink: #f1f5f9            # Slate 100 — primary text
--sribuu-ink-soft: #94a3b8       # Slate 400 — secondary text
--sribuu-on-primary: #ffffff     # Text on dark/green chrome
--sribuu-green: #22c55e          # Income green
--sribuu-red: #ef4444            # Expense red
--sribuu-error: #dc2626          # Validation / destructive

## Typography
--font-family: Arial, Helvetica, sans-serif

nav-link:    13px / 700 / 1  / 0.5px  # Uppercase nav menu
ui-label:    11px / 700 / 1.1 / 0.5px  # Section headers, panel titles, buttons — UPPERCASE
display:     32px / 900 / 1  / 0       # Balance amount, hero wordmark (outlined + shadow)
hero-tagline:15px / 700 / 1.3 / 0      # Balance sub-text
body:        13px / 400 / 1.5 / 0      # Descriptions, tx notes
link:        13px / 700 / 1.4 / 0      # Links
micro:       10px / 400 / 1.3 / 0      # Footer, fine print

## Layout
- **Fixed-width SPA** ~480px centered (mobile-first PWA)
- **Below 720px**: Full-width, single column
- **Above 720px**: Max 480px container centered with chrome border rails
- **Density**: Packed panels with bevel seams, minimal whitespace

## Components

### nav-bar (header)
- Carbon (#020617) slab, 44px tall (touch target)
- Left: "SRIBUU" logo pill (emerald text on white pill, rounded-full)
- Right: user avatar (carbon pill with amber initial)
- Sharp corners, halftone dot bg texture
- Includes bevel highlight top edge (1px rgba(255,255,255,0.08))

### balance-hero (replaces hero-panel)
- Dark emerald (#064e3b) panel with full-width gradient overlay
- Beveled md (6px) corners, bright top edge, chrome-teal shadow below
- Display: 32px outlined+shadow balance amount (white)
- Stats row: income (green), expense (red), count — in micro-uppercase labels
- Bottom-edge: amber "this month" badge

### section-label-bar
- Teal (#1a3a2a) header strip
- Uppercase ui-label title (e.g. "TRANSAKSI")
- Filter button on right (amber pill)
- Sharp corners

### filter-chip-row
- Horizontal scroll row of pill chips
- Default: carbon bg, silver text
- Active: emerald bg, white text, subtle bevel
- Tiny uppercase micro labels

### news-row (transaction item)
- Platinum (#1e293b) row with rounded-sm (4px) corners
- Left: 40px category icon in tinted bg (rounded 10px)
- Middle: category name (uppercase link bold) + notes (body small)
- Right: Amount (emerald for income, red for expense) + date (ink-soft micro)
- Bottom bevel divider (1px hairline)

### quick-action-bar
- Two buttons grid (Tambah / Filter)
- Primary: emerald (#059669) fill, white text, beveled
- Secondary: carbon fill, amber/gold text, beveled
- Rounded-xs (2px) corners, 44px min height

### form-panel (modal)
- Surface (#1e293b) panel, rounded-lg (10px) top corners
- Slide-up animation from bottom
- Section-label-bar header with modal title
- Inputs: surface bg, hairline border, emerald focus ring
- Type switch: segmented control (expense/income) in carbon bg
- Submit button: signal green (#10b981) full-width
- Delete button: red (#dc2626)

### bottom-nav (footer-bar)
- Carbon (#020617) slab with halftone texture
- 3 tabs: Beranda (home), Tambah (+), Keluar (door)
- Active: emerald text + indicator
- Inactive: ink-soft text
- Sharp top edge, safe-area bottom padding

### toast
- Surface (#1e293b) panel, rounded-md, elevated shadow
- Border tinted by type (emerald success, red error, amber info)
- Fixed bottom, centered

### dotted-divider
- 1px dotted hairline (#334155) separator

## Bevel System
Every plate gets:
- Top edge: 1px solid rgba(255,255,255,0.06) — light catch
- Bottom edge: 1px solid rgba(13,148,136,0.3) — chrome-teal shadow
- This creates the "stamped metal" illusion

## Elevation
Level 0 — Inset: recessed fields, darker top edge
Level 1 — Plate: flush panels (default for all containers)
Level 2 — Raised chip: buttons with bright top edge + hard shadow
Level 3 — Command slab: carbon near-black with halftone dots

## Halftone Pattern
Carbon surfaces (nav, bottom-nav) get a repeating radial-gradient dot pattern:
`radial-gradient(circle at 2px 2px, rgba(255,255,255,0.03) 1px, transparent 1px)`
Background-size: 4px 4px

## Touch Targets
All buttons: minimum 44px height
Filter chips: minimum 36px height
Transaction rows: minimum 56px height

## Do's
- Every region is a beveled plate with highlight + shadow edge
- Warm color (amber, gold) for wayfinding only
- Uppercase labels with tracking = the chrome voice
- Hero/balance amounts: outlined + drop-shadowed display type
- Carbon bars with halftone texture
- Panels butt together with thin bevel seams

## Don'ts
- No soft blurred drop shadows — only hard bevel edges
- No rounded corners on nav bars
- No amber/gold for decorative use — only for action signals
- No fluid spacing — packed density is the identity
- Don't flatten dual hierarchy into one bar
