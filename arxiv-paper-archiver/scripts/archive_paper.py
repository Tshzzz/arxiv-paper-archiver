#!/usr/bin/env python3
"""Download and archive an arXiv paper with metadata and extracted text."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import (
    extract_text_from_pdf,
    extracted_text_path,
    fetch_arxiv_by_id,
    iso_now,
    metadata_path,
    paper_archive_dir,
    pdf_path,
    safe_mkdir,
    write_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Archive an arXiv paper by ID.")
    parser.add_argument("--arxiv-id", required=True, help="arXiv identifier, for example 2401.01234.")
    parser.add_argument("--query", default="", help="Original topic query for provenance.")
    parser.add_argument("--archive-dir", required=True, type=Path, help="Root directory for archived papers.")
    args = parser.parse_args()

    paper = fetch_arxiv_by_id(args.arxiv_id)
    if not paper:
        raise SystemExit(f"Unable to find arXiv paper: {args.arxiv_id}")

    archive_root = paper_archive_dir(args.archive_dir, paper.arxiv_id, title=paper.title)
    safe_mkdir(archive_root)

    pdf_output = pdf_path(args.archive_dir, paper.arxiv_id, paper.title)
    if not pdf_output.exists():
        from common import download_file

        download_file(paper.pdf_url, pdf_output)

    source_output = extracted_text_path(args.archive_dir, paper.arxiv_id, title=paper.title)
    extracted_text = source_output.read_text() if source_output.exists() else ""
    if not extracted_text:
        extracted_text = extract_text_from_pdf(pdf_output)
        if extracted_text:
            source_output.write_text(
                "# Extracted Text\n\n"
                f"Source PDF: {pdf_output.name}\n\n"
                f"{extracted_text.strip()}\n"
            )

    metadata = paper.to_dict()
    metadata.update(
        {
            "query": args.query,
            "downloaded_at": iso_now(),
            "archive_dir": str(archive_root),
            "files": {
                "pdf": str(pdf_output),
                "extracted_text": str(source_output) if source_output.exists() else "",
                "ocr_markdown": "",
                "ocr_response": "",
            },
            "extraction_status": "full_text" if extracted_text else "abstract_only",
            "ocr_status": "not_run",
        }
    )
    write_json(metadata_path(args.archive_dir, paper.arxiv_id, title=paper.title), metadata)
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
