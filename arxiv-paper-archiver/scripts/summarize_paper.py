#!/usr/bin/env python3
"""Prepare a summary context packet for the current agent model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import (
    build_paper_context,
    compose_summary_prompt,
    load_metadata,
    load_source_text,
    safe_mkdir,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare a summary context packet for Claude Code or Codex to write the final summary."
    )
    parser.add_argument("--arxiv-id", required=True, help="arXiv identifier.")
    parser.add_argument("--archive-dir", required=True, type=Path, help="Root archive directory.")
    parser.add_argument("--summary-dir", required=True, type=Path, help="Directory for Chinese summaries.")
    args = parser.parse_args()

    metadata = load_metadata(args.archive_dir, args.arxiv_id)
    source_text = load_source_text(args.archive_dir, args.arxiv_id)
    safe_mkdir(args.summary_dir)
    output_path = args.summary_dir / f"{args.arxiv_id}.md"
    context_path = args.summary_dir / f"{args.arxiv_id}.context.md"
    prompt_path = args.summary_dir / f"{args.arxiv_id}.prompt.md"
    context_path.write_text(build_paper_context(metadata, source_text).rstrip() + "\n")
    prompt_path.write_text(
        compose_summary_prompt(metadata, output_path, context_path).rstrip() + "\n"
    )
    print(
        json.dumps(
            {
                "arxiv_id": args.arxiv_id,
                "target_output": str(output_path),
                "context_path": str(context_path),
                "prompt_path": str(prompt_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
