#!/usr/bin/env python3
"""Search arXiv papers by topic and return normalized JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import search_arxiv, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Search arXiv papers and return normalized results.")
    parser.add_argument("--query", required=True, help="Topic or keyword query.")
    parser.add_argument("--max-results", type=int, default=5, help="Maximum number of results to return.")
    parser.add_argument("--json-out", type=Path, help="Optional path to save the JSON results.")
    args = parser.parse_args()

    papers = search_arxiv(args.query, max_results=args.max_results)
    payload = {
        "query": args.query,
        "count": len(papers),
        "results": [paper.to_dict() for paper in papers],
    }
    if args.json_out:
        write_json(args.json_out, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

