# Presentation palette (ACUD logo)

Applies to `presentation.pptx` and any file generated from `presentation.md`. Source: colors sampled from `docs/deliverables/02-video/logo-ACUD.png` (red, black, white). Hex values are written without `#` in OOXML (`<a:srgbClr val="E31B23"/>`) and in pptxgenjs (`color: "E31B23"`). Never use `#` or 8-digit hex there.

## Core colors

| Role | Hex | Use |
| --- | --- | --- |
| Logo red | `E31B23` | Key highlight boxes (for example the "worst signal" box on slide 5, the last step on slide 6), "Synthetic - for training only" banners, chart bars, table header on slide 9, source-line text |
| Logo black | `111111` | Slide 12 background, table headers, flow boxes, dark callouts |
| White | `FFFFFF` | Slide background; text on red or black |
| Light gray | `F1F1F1` | Cards, stat callouts, alternating table rows |
| Body text | `1A1A1A` | Titles and body text on white or light gray |

## Rules

1. Slide background is white. Slide 12 (decision slide) is the only dark slide: black background, white text.
2. Red is the single accent. Use it for the one element a slide wants the eye on, plus the Synthetic banner and chart series. Do not add other hues.
3. Text on red or black is white. Text on white or light gray is `1A1A1A`.
4. Charts: native charts only, bars in `E31B23`, gridlines light gray, axis labels `1A1A1A`.
5. Theme (`ppt/theme/theme1.xml`): `dk1` `111111`, `lt1` `FFFFFF`, `dk2` `111111`, `accent1` `111111`, `accent2` `E31B23`, `accent5` `E31B23`. Prefer theme/scheme colors over hard-coded hex when adding shapes.
6. Origin marks (🟢 real, 🔵 derived, 🟠 generated) are emoji and keep their own colors.
7. Contrast: keep red text on white only for small source lines and labels. Do not put red text on black.

## Old to new mapping (for reference)

| Old | New |
| --- | --- |
| `F4EDDF` cream background | `FFFFFF` |
| `E6DAC1` beige cards | `F1F1F1` |
| `0B1F3A` navy | `111111` |
| `3E5670` steel blue | `E31B23` |
| `B84F08` orange | `E31B23` |
| `1B2430` dark text | `1A1A1A` |

## Checks after any change

- Run `python scripts/office/validate.py deck.pptx` (pptx skill) and fix every failure in the generator.
- Render to images and look at all 12 slides: no text cut off, no low-contrast text, red limited to accents.
- Confirm the grep for leftover old colors returns nothing: `F4EDDF`, `E6DAC1`, `0B1F3A`, `3E5670`, `B84F08`.
