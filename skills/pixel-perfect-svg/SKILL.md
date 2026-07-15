---
name: pixel-perfect-svg
description: Pixel-perfect raster-to-SVG extraction / vectorization. Converts a PNG/JPG (logo, wordmark, icon, flat artwork) into a clean, layered, editable SVG by tracing the actual pixels — NOT by re-drawing in a font or re-prompting an image model. Snaps the image to a flat colour palette, traces each colour as its own binary layer so enclosed counters (holes in O, R, A, D) become real transparent holes, uses polygon mode for type (dead-flat baselines/edges) and spline mode for organic shapes (flames, blobs), removes speckle via connected components, and drops the background to transparency. Use whenever the user wants to "trace to SVG", "pixel-perfect vector", "vectorize this logo", "convert PNG to SVG", "extract an SVG", "make it real vector", or fix a bad AI-generated vector that redrew the font/shapes. Trigger for exact-vector logo work where a generated/rendered raster must become a faithful scalable SVG.
---

# Pixel-Perfect Raster → SVG

Turns a rendered/painted raster (e.g. an AI-generated logo) into a faithful,
editable SVG by **tracing the actual pixels**. This is the correct tool when a
prompt-based vector model (Recraft vector mode, etc.) fails because it *redraws*
its own font and shapes instead of matching the approved artwork.

The CLI lives next to this file: `trace_to_svg.py` (a self-bootstrapping `uv`
script — dependencies install automatically on first run).

## When to use it

- The user approved a raster logo and wants the *same* logo as scalable vector.
- A generated "vector" came back with the wrong font / wrong shapes.
- Counters (holes in O, R, A, D) are filled instead of transparent.
- Letter baselines/edges came out wavy (spline over-smoothing) and must be flat.

## Run it

```bash
# Deps auto-install via uv. Preview rendering needs libcairo on PATH:
#   macOS: brew install cairo, then export DYLD_FALLBACK_LIBRARY_PATH="$(brew --prefix)/lib"
uv run trace_to_svg.py INPUT.png OUTPUT.svg [options]
```

### The moves that make the trace clean (baked into the tool)

1. **Snap to an explicit palette** (`-p`) — kills anti-aliased fuzzy edges that
   otherwise trace into dozens of stray colour slivers.
2. **Trace type in polygon, organic shapes in spline** — `--polygon <hex>` gives
   letters dead-flat baselines and straight sides; `--spline <hex>` keeps flames
   and curves smooth. (Default mode for unlisted colours: `--mode`.)
3. **Drop the background** — `--bg <hex>` or `--auto-bg` makes the paper/canvas
   transparent so you get a real logo layer.
4. **Kill speckle** — `--min-area` drops tiny blobs; `--largest <hex>` keeps only
   the biggest blob for single-shape colours (a lone flame/icon).
5. **`--upscale 2`** before tracing yields finer, straighter edges.
6. **`--preview out.png`** renders a verification PNG (default grey background so
   filled-in counters are obvious).

### Worked example (the RiotWorks wordmark: black type + red flame on cream)

```bash
DYLD_FALLBACK_LIBRARY_PATH="$(brew --prefix)/lib" \
uv run trace_to_svg.py board.png riotworks-logo.svg \
  -p 141414 -p E4342B -p FAF7F2 \
  --bg FAF7F2 \
  --polygon 141414 \
  --spline E4342B \
  --largest E4342B \
  --crop 210,165,2275,740 --upscale 2 \
  --preview riotworks-check.png
```

Ink (`#141414`) traces as flat-bottomed letters with hollow counters; the flame
(`#E4342B`) traces as one smooth shape; the cream paper (`#FAF7F2`) is dropped.

## Verify (do this every time)

After tracing, **render the SVG in a real browser and screenshot it** — a
rasterizer can hide fill-rule/hole bugs. Load the SVG on light, grey, and dark
panels (grey exposes non-transparent counters) and confirm: holes show through,
no clipped shapes, flat baselines. Playwright + Chromium is reliable for this.

## Options reference

`-p/--palette` (repeat) · `-n/--colors` (auto-palette size) · `--bg` (repeat) ·
`--auto-bg` · `--polygon` (repeat) · `--spline` (repeat) · `--mode` ·
`--largest` (repeat) · `--min-area` · `--crop L,T,R,B` · `--upscale` ·
`--filter-speckle` · `--corner-threshold` · `--path-precision` · `--preview` ·
`--preview-bg`.
