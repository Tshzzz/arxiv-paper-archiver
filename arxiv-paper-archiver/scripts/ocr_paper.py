#!/usr/bin/env python3
"""Run GLM-OCR on an archived PDF and store the Markdown result."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import (
    call_glm_ocr,
    encode_file_as_base64_data_url,
    get_bigmodel_api_key,
    load_metadata,
    ocr_markdown_path,
    ocr_response_path,
    pdf_path,
    write_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run GLM-OCR on an archived PDF and save OCR markdown next to the paper."
    )
    parser.add_argument("--arxiv-id", required=True, help="arXiv identifier.")
    parser.add_argument("--archive-dir", required=True, type=Path, help="Root archive directory.")
    parser.add_argument(
        "--api-key",
        default=None,
        help="BigModel API key. Defaults to BIGMODEL_API_KEY or ZHIPU_API_KEY.",
    )
    parser.add_argument(
        "--file-mode",
        choices=("base64", "url"),
        default="base64",
        help="How to send the file to GLM-OCR. base64 uses the local archived PDF; url uses metadata.pdf_url.",
    )
    args = parser.parse_args()

    metadata = load_metadata(args.archive_dir, args.arxiv_id)
    api_key = get_bigmodel_api_key(args.api_key)
    local_pdf = pdf_path(args.archive_dir, args.arxiv_id, metadata.get("title"))
    if not local_pdf.exists():
        raise SystemExit(f"Archived PDF not found: {local_pdf}")

    if args.file_mode == "url":
        file_value = metadata.get("pdf_url") or ""
        if not file_value:
            raise SystemExit("metadata.pdf_url is missing")
    else:
        file_value = encode_file_as_base64_data_url(local_pdf)

    response = call_glm_ocr(file_value=file_value, api_key=api_key)
    md_results = response.get("md_results", "")
    if not isinstance(md_results, str) or not md_results.strip():
        raise SystemExit("GLM-OCR response did not contain md_results")

    md_path = ocr_markdown_path(args.archive_dir, args.arxiv_id)
    md_path.write_text(md_results.rstrip() + "\n")
    write_json(ocr_response_path(args.archive_dir, args.arxiv_id), response)

    metadata["ocr_status"] = "glm_ocr"
    metadata["ocr_generated_at"] = response.get("created")
    files = metadata.setdefault("files", {})
    if isinstance(files, dict):
        files["ocr_markdown"] = str(md_path)
        files["ocr_response"] = str(ocr_response_path(args.archive_dir, args.arxiv_id))
    write_json(Path(args.archive_dir) / args.arxiv_id / "metadata.json", metadata)

    print(
        json.dumps(
            {
                "arxiv_id": args.arxiv_id,
                "ocr_markdown": str(md_path),
                "ocr_response": str(ocr_response_path(args.archive_dir, args.arxiv_id)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
