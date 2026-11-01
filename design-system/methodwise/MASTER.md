# Design System Master File: MethodWise

> **LOGIC:** When building a specific page, first check `design-system/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** MethodWise — Research Methodology Recommendation Assistant  
**Aesthetic Philosophy:** Scholarly Editorial (Typeset Research Journal × Modern Precision Dashboard)  
**Tone & Mood:** Calm, rigorous, epistemologically trustworthy, human, authoritative  
**Primary Design Style:** **Minimalism & Swiss Style** (Clean, spacious, grid-based, functional, objective hierarchy)  
**Supporting Design Style:** **Bento Grid** (Modular information cards, asymmetric spans, hairline borders, consistent 8px rhythm)  
**Style Justification:** Academic scholarship requires clarity, legibility, and high contrast without distraction. Swiss modernism provides rational structure and typographic discipline, while Bento box modularity organizes complex multi-stage methodology recommendations into digestible, scannable units.

---

## 1. Color Palette ("Scholarly Editorial" Paper & Ink)

Colour is used with strict intent: Indigo for navigation and primary actions; Ochre for emphasis, attention, and highlights; Teal for validation pass and empirical integrity; Red exclusively for failures and ethical alerts. **Maximum 3 hues per view.**

| Role | Hex Code | Token / CSS Variable | Usage & Semantics |
|------|----------|----------------------|-------------------|
| **Paper Background** | `#FAF7F2` | `--color-bg-paper` | Base canvas, warm editorial tone, zero glare |
| **Card / Surface** | `#FFFFFF` | `--color-surface` | Pure white content cards, forms, and containers |
| **Surface Subtle** | `#F5F2EB` | `--color-surface-subtle` | Secondary panels, table headers, code backgrounds |
| **Hairline Border** | `#E7E2D9` | `--color-border` | Hairline card boundaries (1px solid) |
| **Border Subtle** | `#EFECE6` | `--color-border-subtle` | Table row dividers, subtle card separators |
| **Deep Ink** | `#0F172A` | `--color-ink` | Headings, primary labels, maximum contrast (14.2:1) |
| **Body Ink** | `#334155` | `--color-ink-body` | Paragraph body copy, readable contrast (8.4:1) |
| **Muted Ink** | `#64748B` | `--color-ink-muted` | Metadata, captions, breadcrumbs, helper notes (4.8:1) |
| **Primary Brand** | `#3730A3` | `--color-primary` | Deep academic indigo (logo, primary CTA, active page) |
| **Primary Hover** | `#312E81` | `--color-primary-hover` | Button hover and active states |
| **Primary Subtle** | `#EEF2FF` | `--color-primary-subtle` | Active nav badge, selected chip background |
| **Accent Ochre** | `#B45309` | `--color-accent` | Scholarly ochre / gold (attention, key paradigms) |
| **Accent Subtle** | `#FEF3C7` | `--color-accent-subtle` | Highlight callouts, confidence badge surface |
| **Success Teal** | `#0F766E` | `--color-success` | Validated, rubric pass (>= 75%), reference match |
| **Success Subtle** | `#F0FDFA` | `--color-success-subtle` | Pass badge fill, verified evidence chip |
| **Warning Amber** | `#B45309` | `--color-warning` | Review status, parameter notices |
| **Danger Red** | `#B91C1C` | `--color-danger` | Edge case rejection, vulnerable cohort alert |
| **Danger Subtle** | `#FEF2F2` | `--color-danger-subtle` | Vulnerable population banner fill |

**Strict Color Prohibitions:**
- ❌ No purple/violet or magenta gradients
- ❌ No neon, glow, or bloom drop-shadows
- ❌ No rainbow progress bars or uncalibrated multi-color tag clouds

---

## 2. Typography Hierarchy & Tokens

- **Heading Display:** `Crimson Pro` (Google Fonts, weights 600, 700) — refined, scholarly serif for H1–H3.
- **UI & Body Sans:** `Atkinson Hyperlegible` / `Inter` (Google Fonts, weights 400, 500, 600, 700) — engineered for legibility.
- **Tabular & Code:** `JetBrains Mono` (Google Fonts, weights 400, 500) — monospace with `font-variant-numeric: tabular-nums` for scores, power stats, and latency.

```css
@import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&family=Crimson+Pro:ital,wght@0,500;0,600;0,700;1,500;1,600&family=JetBrains+Mono:wght@400;500;600&display=swap');
```

### Type Scale
| Level | Font Family | Size | Weight | Line Height | Tracking |
|-------|-------------|------|--------|-------------|----------|
| **Display / Hero** | `Crimson Pro`, serif | `44px` / `2.75rem` | 700 | 1.15 | `-0.02em` |
| **Title / H1** | `Crimson Pro`, serif | `32px` / `2.0rem` | 700 | 1.20 | `-0.015em` |
| **Section / H2** | `Crimson Pro`, serif | `24px` / `1.5rem` | 600 | 1.25 | `-0.01em` |
| **Subhead / H3** | `Atkinson Hyperlegible`, sans | `18px` / `1.125rem` | 700 | 1.35 | `0` |
| **Body Large** | `Atkinson Hyperlegible`, sans | `16px` / `1.0rem` | 400 | 1.60 | `0` |
| **Body Regular** | `Atkinson Hyperlegible`, sans | `14px` / `0.875rem` | 400 | 1.55 | `0` |
| **Caption / Meta** | `Atkinson Hyperlegible`, sans | `12px` / `0.75rem` | 600 | 1.40 | `0.02em` (uppercase) |
| **Scores / Metrics** | `JetBrains Mono`, monospace | `28px` / `1.75rem` | 600 | 1.00 | `tabular-nums` |

---

## 3. Surface Architecture & Spacing

- **Cards:** Hairline borders (`1px solid #E7E2D9`), `12px` border-radius, background `#FFFFFF`.
- **Shadows:** Very soft, natural ambient depth only:
  - Base Card: `box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04), 0 1px 2px rgba(15, 23, 42, 0.02);`
  - Hover Lift: `transform: translateY(-1.5px); box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.07);`
- **Spacing Grid:** Strict 8px mathematical rhythm (`8px`, `16px`, `24px`, `32px`, `48px`).

---

## 4. Signature Editorial Elements

1. **"Method Map" Hero Visual:**
   - Inline SVG of a branching epistemological tree: Root inquiry → Paradigm branches (Quantitative, Qualitative, Mixed) → Design leaves (RCT, Quasi-exp, IPA, Reflexive TA, Convergent Parallel).
   - Drawn with `#3730A3` and `#B45309` strokes on paper/cream tones.
   - Smooth 250ms fade-in, disabled under `@media (prefers-reduced-motion: reduce)`.
2. **"Methodology Brief" Document Layout:**
   - Results rendered as an academic paper brief: numbered clauses (`1. Scope`, `2. Sampling`, `3. Instruments`, `4. Analytics`, `5. Ethics`, `6. Alternatives`, `7. Phased Roadmap`).
   - Sticky / compact table of contents.
   - Academic abstract header block showing paradigm, design, confidence, and validation score.
3. **"Evidence Ribbon":**
   - High-trust strip under the abstract header showing the 3 independent checks:
     - `[Icon] Rubric Score: 94% (PASS)`
     - `[Icon] Gold Reference: REF-001 (MATCH)`
     - `[Icon] Deterministic Rules: Zero Violations`
   - Never relies on color alone; always pairs SVG icon + label + numeric score.
4. **Ethics Marginal Callout:**
   - Deep amber/red bordered marginal note with an icon and clear banner for vulnerable cohorts and mandatory IRB approval.
5. **Segmented Confidence Meter:**
   - 3-step discrete meter: `[Low | Medium | High]` with explicit active step highlighted in ochre or teal.
6. **Timeline Execution Roadmap:**
   - Numbered circular nodes connected by a subtle vertical border track (`2px solid #E7E2D9`).
7. **Scholarly Plotly Chart System:**
   - Palette: Indigo `#3730A3`, Ochre `#B45309`, Teal `#0F766E`, Slate `#64748B`.
   - Direct inline data labels; no heavy floating legend boxes.
   - Accessible text summary paragraph placed immediately below every visualization.

---

## 5. Domain Search Findings

### Style Domain (`--domain style`)
- **Primary:** `Minimalism & Swiss Style` (Clean, simple, functional white space, high contrast, geometric, grid-based, rational typography).
- **Supporting:** `Bento Box Grid` (Modular cards, varied spans, Apple/academic dashboard tiles, clean hierarchy, hover lift <= 2px).

### Typography Domain (`--domain typography`)
- **Pairing:** `Crimson Pro` (Display Serif) + `Atkinson Hyperlegible` (Accessible Sans).
- **Rationale:** Crimson Pro gives academic gravitas and editorial elegance; Atkinson Hyperlegible was developed by the Braille Institute for maximum character distinction and accessibility.

### Chart Domain (`--domain chart`)
- **Score Gauges & Bullets:** Segmented arc / bullet meter with qualitative thresholds (0–50 Fail, 50–74 Review, 75–100 Pass) labeled with text and tabular figures.
- **Rubric Horizontal Bar:** 5 criteria on a 0–5 scale, sorted by score or fixed rubric order with direct value callouts (`5.0 / 5.0`).
- **Benchmark Grouped Bars:** Side-by-side comparison with high-contrast color pairing (Indigo vs. Slate vs. Ochre), zero clutter, subtle grid lines on paper background.

### UX Domain (`--domain ux`)
- **Forms & Validation:** Inline helper captions, progressive disclosure for research constraints, character count guidance, deterministic input screening with actionable suggestions.
- **Progress & Loading:** 4-stage pipeline execution state tracker with clear step labels (`Stage 1 of 4: Validating...`).
- **Empty States:** Meaningful SVG icon, clear explanation, and primary action button (never a blank white screen).
- **Badges & Chips:** Semantic markup with icon + text; never color alone. Hairline border + subtle tinted fill.
- **Tables:** Sticky header, dense but readable padding (`10px 14px`), monospace tabular numerals for metrics, text-labeled status pills.

### Icons Domain (`--domain icons`)
- **Library:** Phosphor / Lucide clean geometric outline SVGs (16px and 20px).
- **Rule:** Strict prohibition of raw emojis in UI components. Native Material symbols in sidebar navigation only (`:material/icon_name:`).

---

## 6. Accessibility & Pre-Delivery Checklist (Mandatory)

- [x] Text contrast >= 4.5:1 on both `#FAF7F2` paper and `#FFFFFF` cards.
- [x] UI component borders and icons >= 3:1 contrast against background.
- [x] `cursor: pointer` on all buttons, links, clickable chips, and interactive cards.
- [x] Focus ring: `2px solid #3730A3` with `2px` offset visible on keyboard tab navigation.
- [x] Status is NEVER conveyed by color alone (always icon + text label).
- [x] Responsive layout across 375px, 768px, 1024px, and 1440px viewports.
- [x] `prefers-reduced-motion` media query respected (transitions <= 200ms or none).
- [x] No raw tracebacks or uncaught exceptions shown to the user.
- [x] Streamlit default clutter hidden while keeping sidebar toggle fully functional.
