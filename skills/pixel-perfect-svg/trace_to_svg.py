#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["click", "vtracer", "pillow", "numpy", "scipy", "cairosvg"]
# ///
"""Pixel-perfect raster -> SVG extraction.

Snaps an image to a flat colour palette, then traces each colour as its own
binary layer so enclosed counters (the holes in O, R, A, D ...) become real
transparent holes. Type / geometric colours can be traced in *polygon* mode for
dead-flat straight edges; organic colours (flames, blobs) in *spline* mode for
smooth curves. Speckle is removed via connected-component filtering, and
background colours can be dropped to transparency.

Run with uv (deps auto-install):
    uv run trace_to_svg.py INPUT.png OUTPUT.svg [options]
"""
import os
import re
import tempfile
from collections import Counter
from pathlib import Path

import click
import numpy as np
import vtracer
from PIL import Image
from scipy import ndimage

SVG_NS = "http://www.w3.org/2000/svg"


def norm_hex(value: str) -> str:
    return value.lstrip("#").lower()


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    h = norm_hex(value)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def load_image(path: str, crop: str | None, upscale: float) -> Image.Image:
    image = Image.open(path).convert("RGB")
    if crop:
        left, top, right, bottom = (int(v) for v in crop.split(","))
        image = image.crop((left, top, right, bottom))
    if upscale and upscale != 1:
        image = image.resize(
            (round(image.width * upscale), round(image.height * upscale)), Image.LANCZOS
        )
    return image


def auto_palette(image: Image.Image, count: int) -> list[str]:
    reduced = image.quantize(colors=count).convert("RGB")
    swatches = sorted(reduced.getcolors(count * 4) or [], reverse=True)
    return ["".join(f"{c:02x}" for c in rgb) for _, rgb in swatches[:count]]


def classify(image: Image.Image, palette: list[str]) -> np.ndarray:
    pixels = np.asarray(image).astype(int)
    swatches = np.asarray([hex_to_rgb(h) for h in palette])
    distances = ((pixels[:, :, None, :] - swatches[None, None, :, :]) ** 2).sum(3)
    return distances.argmin(2)


def corner_background(index_map: np.ndarray, palette: list[str]) -> str:
    corners = [
        index_map[0, 0],
        index_map[0, -1],
        index_map[-1, 0],
        index_map[-1, -1],
    ]
    return palette[Counter(int(c) for c in corners).most_common(1)[0][0]]


def keep_components(mask: np.ndarray, largest: bool, min_area: int) -> np.ndarray:
    labels, count = ndimage.label(mask)
    if count == 0:
        return mask
    sizes = ndimage.sum(np.ones_like(labels), labels, range(1, count + 1))
    if largest:
        return labels == (1 + int(np.argmax(sizes)))
    keep = np.zeros_like(mask, dtype=bool)
    for label, size in enumerate(sizes, start=1):
        if size >= min_area:
            keep |= labels == label
    return keep


def trace_layer(
    mask: np.ndarray,
    fill_hex: str,
    mode: str,
    filter_speckle: int,
    corner_threshold: int,
    path_precision: int,
) -> str:
    if not mask.any():
        return ""
    layer = Image.fromarray(np.where(mask, 0, 255).astype("uint8"), "L")
    params = dict(
        colormode="binary",
        mode=mode,
        filter_speckle=filter_speckle,
        corner_threshold=corner_threshold,
        length_threshold=4.0,
        path_precision=path_precision,
    )
    if mode == "spline":
        params["splice_threshold"] = 45
    with tempfile.TemporaryDirectory() as work:
        src = os.path.join(work, "mask.png")
        dst = os.path.join(work, "mask.svg")
        layer.save(src)
        vtracer.convert_image_to_svg_py(src, dst, **params)
        raw = Path(dst).read_text()
    paths = []
    for path in re.findall(r"<path[^>]*?/>", raw):
        found = re.search(r'fill="(#[0-9a-fA-F]{6})"', path)
        if found and found.group(1).lower() in ("#ffffff", "#fefefe"):
            continue
        paths.append(re.sub(r'fill="#[0-9a-fA-F]{6}"', f'fill="#{norm_hex(fill_hex)}"', path))
    return "\n".join(paths)


@click.command()
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False))
@click.argument("output_path", type=click.Path(dir_okay=False))
@click.option("--palette", "-p", multiple=True, help="Hex colour to snap to (repeatable). Omit to auto-detect.")
@click.option("--colors", "-n", default=4, show_default=True, help="Auto palette size when --palette is omitted.")
@click.option("--bg", multiple=True, help="Hex colour(s) to drop to transparency (repeatable).")
@click.option("--auto-bg", is_flag=True, help="Drop the colour found in the image corners.")
@click.option("--polygon", multiple=True, help="Trace these hex colours in polygon mode (flat edges).")
@click.option("--spline", multiple=True, help="Trace these hex colours in spline mode (smooth curves).")
@click.option("--mode", type=click.Choice(["polygon", "spline"]), default="spline", show_default=True,
              help="Default mode for colours not named in --polygon/--spline.")
@click.option("--largest", multiple=True, help="Keep only the largest blob for these hex colours (e.g. a single icon).")
@click.option("--min-area", default=60, show_default=True, help="Drop connected components smaller than this many pixels.")
@click.option("--crop", default=None, help="Crop before tracing: 'left,top,right,bottom'.")
@click.option("--upscale", default=1.0, show_default=True, help="Upscale factor before tracing (finer straight edges).")
@click.option("--filter-speckle", default=8, show_default=True)
@click.option("--corner-threshold", default=60, show_default=True)
@click.option("--path-precision", default=8, show_default=True)
@click.option("--preview", default=None, type=click.Path(dir_okay=False), help="Also render a verification PNG here.")
@click.option("--preview-bg", default="8A8A8A", show_default=True, help="Background for the preview PNG (hex).")
def main(input_path, output_path, palette, colors, bg, auto_bg, polygon, spline, mode,
         largest, min_area, crop, upscale, filter_speckle, corner_threshold, path_precision,
         preview, preview_bg):
    """Trace INPUT_PATH into a clean, layered SVG at OUTPUT_PATH."""
    image = load_image(input_path, crop, upscale)
    swatches = [norm_hex(c) for c in palette] or auto_palette(image, colors)
    index_map = classify(image, swatches)

    dropped = {norm_hex(c) for c in bg}
    if auto_bg:
        dropped.add(norm_hex(corner_background(index_map, swatches)))

    polygon_set = {norm_hex(c) for c in polygon}
    spline_set = {norm_hex(c) for c in spline}
    largest_set = {norm_hex(c) for c in largest}

    layers = []
    for idx, swatch in enumerate(swatches):
        if swatch in dropped:
            continue
        mask = keep_components(index_map == idx, swatch in largest_set, min_area)
        layer_mode = "polygon" if swatch in polygon_set else "spline" if swatch in spline_set else mode
        body = trace_layer(mask, swatch, layer_mode, filter_speckle, corner_threshold, path_precision)
        if body:
            layers.append(body)

    width, height = image.size
    svg = (
        f'<svg xmlns="{SVG_NS}" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">\n' + "\n".join(layers) + "\n</svg>\n"
    )
    Path(output_path).write_text(svg)
    click.echo(f"wrote {output_path}  ({len(layers)} colour layers, palette: {', '.join('#'+s for s in swatches)})")

    if preview:
        import cairosvg

        cairosvg.svg2png(url=output_path, write_to=preview, output_width=min(2000, width * 2),
                         background_color=f"#{norm_hex(preview_bg)}")
        click.echo(f"preview  {preview}")


if __name__ == "__main__":
    main()
