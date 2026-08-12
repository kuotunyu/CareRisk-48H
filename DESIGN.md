---
name: CareRisk 48H
description: A daylight evidence console for auditable, synthetic-only clinical ML research demonstrations.
colors:
  canvas: "#F4F7FA"
  surface: "#FFFFFF"
  ink: "#102A43"
  structural-navy: "#082B4C"
  method-teal: "#087F8C"
  review-amber: "#A16207"
  quiet-border: "#CAD5E0"
  muted-copy: "#52677A"
  invalid-red: "#B42318"
typography:
  title:
    fontFamily: "Segoe UI Variable, Segoe UI, system-ui, sans-serif"
    fontSize: "clamp(32px, 3vw, 38px)"
    fontWeight: 700
    lineHeight: 1.12
    letterSpacing: "-0.025em"
  body:
    fontFamily: "Segoe UI Variable, Segoe UI, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Segoe UI Variable, Segoe UI, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 700
    lineHeight: 1.5
  code:
    fontFamily: "ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  control: "8px"
  evidence: "10px"
  frame: "12px"
spacing:
  compact: "8px"
  control: "12px"
  section: "16px"
  panel: "20px"
  frame: "24px"
components:
  button-primary:
    backgroundColor: "{colors.structural-navy}"
    textColor: "{colors.surface}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    height: "46px"
  evidence-container:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.frame}"
    padding: "{spacing.frame}"
  audit-disclosure:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.evidence}"
    height: "44px"
---

# Design System: CareRisk 48H

## Overview

**Creative North Star: "The Auditable Research Workstation"**

CareRisk 48H uses a restrained daylight workstation rather than an EHR, clinical monitor, or marketing dashboard. The interface should feel precise and inspectable: one structural navy field, white evidence surfaces, measured rules, compact rows, and technical terms surrounded by plain Traditional Chinese explanations.

Information density is purposeful. The result never outranks its evidence boundary, and secondary machine detail stays available without displacing the primary reviewer path.

**Key Characteristics:**

- Evidence-led hierarchy with the gate disposition before the synthetic score.
- Flat daylight surfaces separated by borders and tonal contrast, not decorative shadows.
- Traditional Chinese (`zh-TW`) first; established technical terms remain in their original language.
- Synthetic and non-clinical limitations remain visible in the primary hierarchy.

## Colors

The palette combines cool paper neutrals with a deep structural field and a single method accent.

### Primary

- **Structural Navy:** Header fields and the primary action; it establishes the research-console frame.

### Secondary

- **Method Teal:** Evidence-sequence markers, permitted-output status, and the synthetic demonstration score.
- **Review Amber:** Reserved for `abstention` and human-review states; always paired with text.
- **Invalid Red:** Reserved for schema/input failure, never for risk classification.

### Neutral

- **Cool Canvas:** The page background that separates the tool from its evidence surfaces.
- **Evidence White:** Primary reading and data surfaces.
- **Research Ink:** Headings, values, and core copy.
- **Muted Copy:** Explanations, boundaries, and metadata.
- **Quiet Border:** Frames, rules, and table separation.

**The Evidence Color Rule.** Teal communicates method or output availability, amber communicates review, and red communicates invalid input; none of them classify a person's clinical state.

## Typography

**Title and Body Font:** Segoe UI Variable with Segoe UI and system UI fallbacks
**Code Font:** The platform monospace stack, used only for JSON, feature names, and machine values

**Character:** A high-legibility UI workhorse keeps the console fast and dependency-free. Hierarchy comes from size and weight rather than decorative display styling.

### Hierarchy

- **Product title:** Bold, responsive 32–38 px on desktop and 34 px on mobile, with a compact 1.12 line height.
- **Section heading:** Semibold 24–26 px with a 1.25 line height.
- **Body:** Regular 17 px with a 1.5 line height.
- **Control:** Semibold 17 px, never reduced for density.
- **Label:** 15 px; uppercase and tracking are reserved for meaningful phase markers.
- **Code:** 14 px with a 1.5 line height and bounded scrolling.

**The Read Without Zoom Rule.** Body and controls stay at 17 px or larger, labels at 15 px or larger, and machine detail at 14 px or larger.

## Layout

The application centers within a 1,280 px maximum container using 16–20 px desktop padding. Its dominant console is a 38/62 scenario-to-evidence grid with one shared border. In an allowed desktop result at 1,000 px or wider, the guard and research output use a compact 56/44 inner grid. Below the console, the analytic region uses a 3/2 plot-to-signal split. Empty analytic regions occupy no space.

Below 720 px, all regions become one column in task order: header, safety notice, fixture, primary action, result, evidence, then advanced detail. Mobile padding tightens to 12–16 px while the primary action remains at least 44 px high and inside the first 390×844 viewport. The page must never introduce horizontal scrolling.

**The Evidence Before Output Rule.** Reading order always establishes synthetic provenance and evidence-gate disposition before displaying a precise research output.

## Elevation & Depth

The system is flat by default and uses no shadows. Depth comes from the cool canvas behind white evidence fields, a single dominant console border, thin internal rules, and the navy header plane.

**The Flat Evidence Rule.** Do not stack cards or combine a border and shadow; use one container boundary and measured rows.

## Shapes

Controls use an 8 px radius, secondary evidence surfaces use 10 px, and the dominant frame uses 12 px. Borders are 1 px and cool-toned. Small outline SVG icons use a consistent 24 px box, round joins, and a 2 px stroke. Pills, gauges, traffic lights, and decorative badge clusters are outside the system.

## Components

### Primary Button

- **Shape:** Full-width rectangular control with gently rounded 8 px corners and a 46 px height; all secondary controls remain at least 44 px.
- **Color:** Structural navy with white text; hover deepens the navy.
- **Focus:** A visible teal outline and translucent focus ring remain outside the control edge.

### Evidence Rows

- **Structure:** Key and value share one row on desktop, separated by quiet horizontal rules.
- **Mobile:** Key and value remain compact inline rows at the 390 px target and stack only below 360 px; they never become individual cards.
- **Meaning:** Labels use muted copy; validated or derived values use research ink and stronger weight.

### Status Line

- **Available:** A full teal border, outline SVG icon, and explicit text.
- **Review:** A pale amber field with a complete amber border and explicit `abstention` explanation.
- **Invalid:** A pale red field with a complete muted-red border, recovery copy, and no stale result.

### Disclosures

- **Style:** White, thin-bordered, 8–10 px corners, and at least 44 px high.
- **Behavior:** Synthetic JSON and machine output are collapsed by default; opened machine content has bounded internal scrolling.

### Evidence Console

- **Desktop:** One 38/62 frame with a single vertical divider.
- **Allowed result:** At 1,000 px or wider, one evidence-first 56/44 inner grid places the guard summary beside the research output without changing DOM order.
- **Mobile:** One stacked frame with a horizontal divider between fixture and result.
- **Content:** Avoid nested cards; use headings, rows, tables, and disclosures.

## Do's and Don'ts

### Do:

- **Do** keep synthetic provenance and the non-clinical boundary visible without opening a disclosure.
- **Do** put `evidence gates` before the score and use `research operating point` for the threshold.
- **Do** use Traditional Chinese for instructions and explanations while preserving technical terms such as `calibration`, `abstention`, `missingness`, and `OOD`.
- **Do** derive every displayed count, signal, and state from validated synthetic input or the actual inference result.

### Don't:

- **Don't** present the demo as an EHR, diagnostic monitor, patient workflow, or clinical decision-support system.
- **Don't** use diagnostic red/green traffic lights, gauges, gradients, glass, glow, emoji, or decorative stock imagery.
- **Don't** expose precise probability after `abstention`, imply causal model signals, or describe the research operating point as clinically validated.
- **Don't** let JSON, empty output containers, or redundant hierarchy displace the primary action from the first viewport.
