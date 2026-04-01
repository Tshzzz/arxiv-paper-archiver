#!/usr/bin/env python3
"""Render OCR bbox placeholders into real figure images and a Markdown copy."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PLACEHOLDER_RE = re.compile(r"!\[\]\(page=(\d+),bbox=\[(\d+), (\d+), (\d+), (\d+)\]\)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render figure placeholders from OCR markdown into PNG files and a renderable Markdown copy."
    )
    parser.add_argument("--pdf", required=True, type=Path, help="Path to the source PDF.")
    parser.add_argument("--ocr-md", required=True, type=Path, help="Path to OCR markdown containing page/bbox placeholders.")
    parser.add_argument(
        "--ocr-response-json",
        type=Path,
        help="Optional GLM-OCR raw response JSON. When provided, per-page OCR width/height are read from data_info.pages.",
    )
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory to write figures and rendered markdown.")
    parser.add_argument(
        "--ocr-page-width",
        type=int,
        default=1700,
        help="Width of the OCR coordinate system used for bbox values.",
    )
    parser.add_argument(
        "--ocr-page-height",
        type=int,
        default=2200,
        help="Height of the OCR coordinate system used for bbox values.",
    )
    parser.add_argument(
        "--zoom",
        type=float,
        default=4.0,
        help="PDF render zoom before cropping.",
    )
    args = parser.parse_args()

    import fitz
    from PIL import Image

    output_dir = args.output_dir
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    markdown = args.ocr_md.read_text()
    doc = fitz.open(args.pdf)
    page_sizes: list[tuple[int, int]] = []
    if args.ocr_response_json and args.ocr_response_json.exists():
        response = json.loads(args.ocr_response_json.read_text())
        pages = response.get("data_info", {}).get("pages", [])
        if isinstance(pages, list):
            for page in pages:
                if isinstance(page, dict) and "width" in page and "height" in page:
                    page_sizes.append((int(page["width"]), int(page["height"])))

    figure_count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal figure_count
        page_index = int(match.group(1))
        x0, y0, x1, y1 = [int(match.group(i)) for i in range(2, 6)]
        page = doc[page_index]
        pix = page.get_pixmap(matrix=fitz.Matrix(args.zoom, args.zoom), alpha=False)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        if page_index < len(page_sizes):
            ocr_page_width, ocr_page_height = page_sizes[page_index]
        else:
            ocr_page_width, ocr_page_height = args.ocr_page_width, args.ocr_page_height

        sx = pix.width / ocr_page_width
        sy = pix.height / ocr_page_height

        crop_box = (
            max(0, int(round(x0 * sx))),
            max(0, int(round(y0 * sy))),
            min(pix.width, int(round(x1 * sx))),
            min(pix.height, int(round(y1 * sy))),
        )
        cropped = image.crop(crop_box)
        figure_count += 1
        filename = f"figure-{figure_count:02d}-page-{page_index + 1}.png"
        output_path = figures_dir / filename
        cropped.save(output_path)
        return f"![](./figures/{filename})"

    rendered_markdown = PLACEHOLDER_RE.sub(replace, markdown)
    rendered_path = output_dir / "ocr.rendered.md"
    rendered_path.write_text(rendered_markdown)
    print(rendered_path)


if __name__ == "__main__":
    main()
