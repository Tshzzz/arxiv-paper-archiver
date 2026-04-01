#!/usr/bin/env python3
"""Find top-N hot arXiv papers for an arbitrary topic."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from common import ArxivPaper, iso_now, search_arxiv, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Find top-N hot arXiv papers for an arbitrary topic by combining "
            "multi-query consensus, ranking position, recency, and topic relevance."
        )
    )
    parser.add_argument("--topic", required=True, help="Topic or research problem to explore.")
    parser.add_argument(
        "--alias",
        action="append",
        default=[],
        help="Optional extra English query alias. Repeat for multiple aliases.",
    )
    parser.add_argument("--top-n", type=int, default=10, help="How many hot papers to return.")
    parser.add_argument(
        "--per-query",
        type=int,
        default=12,
        help="How many papers to collect from each query view.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Optional path to save the JSON report.",
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        help="Optional path to save the Markdown report.",
    )
    return parser.parse_args()


@dataclass
class Evidence:
    query: str
    mode: str
    rank: int

    def to_dict(self) -> dict[str, str | int]:
        return {"query": self.query, "mode": self.mode, "rank": self.rank}


@dataclass
class Candidate:
    paper: ArxivPaper
    evidences: list[Evidence] = field(default_factory=list)

    def add(self, evidence: Evidence) -> None:
        self.evidences.append(evidence)

    @property
    def matched_queries(self) -> list[str]:
        return sorted({item.query for item in self.evidences})

    @property
    def matched_modes(self) -> list[str]:
        return sorted({item.mode for item in self.evidences})

    def best_rank(self) -> int:
        return min(item.rank for item in self.evidences)


def normalize_queries(topic: str, aliases: list[str]) -> list[str]:
    candidates = [topic, *aliases]
    expanded: list[str] = []
    for item in candidates:
        if not item:
            continue
        parts = re.split(r"[;,/]|(?:\s+\|\s+)", item)
        for part in parts:
            cleaned = re.sub(r"\s+", " ", part).strip()
            if cleaned:
                expanded.append(cleaned)
    deduped: list[str] = []
    seen: set[str] = set()
    for item in expanded:
        key = item.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def tokenize_topic(text: str) -> list[str]:
    return [token for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9+\-_.]{1,}", text.lower()) if len(token) > 1]


def collect_candidates(queries: list[str], per_query: int) -> dict[str, Candidate]:
    candidates: dict[str, Candidate] = {}
    seen_views: dict[tuple[str, str], set[str]] = defaultdict(set)
    for query in queries:
        for mode, sort_by in (("relevance", "relevance"), ("recent", "lastUpdatedDate")):
            papers = search_arxiv(query, max_results=per_query, sort_by=sort_by)
            for index, paper in enumerate(papers, start=1):
                key = (query, mode)
                if paper.arxiv_id in seen_views[key]:
                    continue
                seen_views[key].add(paper.arxiv_id)
                candidate = candidates.setdefault(paper.arxiv_id, Candidate(paper=paper))
                candidate.add(Evidence(query=query, mode=mode, rank=index))
    return candidates


def parse_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def compute_recency_score(paper: ArxivPaper) -> float:
    updated = parse_timestamp(paper.updated) or parse_timestamp(paper.published)
    if not updated:
        return 0.0
    age_days = max((datetime.now(UTC) - updated).total_seconds() / 86400.0, 0.0)
    return math.exp(-age_days / 45.0)


def compute_topic_overlap_score(paper: ArxivPaper, topic_tokens: list[str], queries: list[str]) -> tuple[float, list[str]]:
    haystack = f"{paper.title}\n{paper.abstract}".lower()
    if not topic_tokens and not queries:
        return 0.3, []
    matched_tokens = [token for token in topic_tokens if token in haystack]
    token_score = len(set(matched_tokens)) / max(len(set(topic_tokens)), 1) if topic_tokens else 0.0
    phrase_hits = [query for query in queries if len(query) > 3 and query.lower() in haystack]
    phrase_bonus = min(0.35, 0.15 * len(phrase_hits))
    score = min(1.0, token_score + phrase_bonus)
    return score, matched_tokens[:8]


def compute_rank_score(evidences: list[Evidence], per_query: int, query_count: int) -> tuple[float, float]:
    if not evidences:
        return 0.0, 0.0
    rank_points = 0.0
    max_rank_points = 2 * query_count
    for evidence in evidences:
        rank_points += max(0.0, (per_query - evidence.rank + 1) / per_query)
    consensus = len({item.query for item in evidences}) / max(query_count, 1)
    rank_score = min(rank_points / max(max_rank_points, 1), 1.0)
    return rank_score, consensus


def build_hot_reasons(
    candidate: Candidate,
    matched_tokens: list[str],
    recency_score: float,
    consensus_score: float,
) -> list[str]:
    reasons = [
        f"出现在 {len(candidate.matched_queries)} 个查询视角中：{', '.join(candidate.matched_queries)}",
        f"同时进入 {', '.join(candidate.matched_modes)} 排序视图，最佳名次第 {candidate.best_rank()}",
    ]
    if matched_tokens:
        reasons.append(f"标题或摘要命中了主题词：{', '.join(sorted(set(matched_tokens))[:6])}")
    if recency_score >= 0.7:
        reasons.append(f"更新较新（{candidate.paper.updated or candidate.paper.published}）")
    elif consensus_score >= 0.7:
        reasons.append("多查询共现度较高")
    return reasons


def build_payload(topic: str, queries: list[str], candidates: dict[str, Candidate], top_n: int, per_query: int) -> dict:
    topic_tokens = tokenize_topic(" ".join(queries))
    scored_results: list[dict] = []
    for candidate in candidates.values():
        recency_score = compute_recency_score(candidate.paper)
        topic_score, matched_tokens = compute_topic_overlap_score(candidate.paper, topic_tokens, queries)
        rank_score, consensus_score = compute_rank_score(candidate.evidences, per_query=per_query, query_count=len(queries))
        hot_score = round(100 * (0.38 * consensus_score + 0.27 * rank_score + 0.2 * recency_score + 0.15 * topic_score), 2)
        scored_results.append(
            {
                "title": candidate.paper.title,
                "arxiv_id": candidate.paper.arxiv_id,
                "arxiv_url": candidate.paper.entry_url,
                "pdf_url": candidate.paper.pdf_url,
                "published": candidate.paper.published,
                "updated": candidate.paper.updated,
                "authors": candidate.paper.authors,
                "categories": candidate.paper.categories,
                "abstract": candidate.paper.abstract,
                "hot_score": hot_score,
                "hot_reasons": build_hot_reasons(candidate, matched_tokens, recency_score, consensus_score),
                "matched_queries": candidate.matched_queries,
                "matched_modes": candidate.matched_modes,
                "evidence": [item.to_dict() for item in sorted(candidate.evidences, key=lambda item: (item.mode, item.query, item.rank))],
                "scores": {
                    "consensus": round(consensus_score, 4),
                    "rank": round(rank_score, 4),
                    "recency": round(recency_score, 4),
                    "topic_relevance": round(topic_score, 4),
                },
            }
        )
    scored_results.sort(
        key=lambda item: (
            item["hot_score"],
            item["scores"]["consensus"],
            item["scores"]["rank"],
            item["scores"]["recency"],
        ),
        reverse=True,
    )
    ranked = []
    for index, item in enumerate(scored_results[:top_n], start=1):
        ranked.append({"rank": index, **item})
    return {
        "generated_at": iso_now(),
        "topic": topic,
        "queries_used": queries,
        "top_n": top_n,
        "candidate_count": len(candidates),
        "scoring_method": {
            "summary": "Hotness is estimated from multi-query consensus, rank position, recency, and topic relevance.",
            "weights": {
                "consensus": 0.38,
                "rank": 0.27,
                "recency": 0.2,
                "topic_relevance": 0.15,
            },
        },
        "results": ranked,
    }


def render_markdown(payload: dict) -> str:
    lines = [
        f"# 热门论文 Top {payload['top_n']}",
        "",
        f"- 主题: {payload['topic']}",
        f"- 生成时间: {payload['generated_at']}",
        f"- 查询视角: {', '.join(payload['queries_used'])}",
        f"- 候选总数: {payload['candidate_count']}",
        "",
    ]
    for item in payload["results"]:
        lines.extend(
            [
                f"## {item['rank']}. {item['title']}",
                "",
                f"- arXiv ID: {item['arxiv_id']}",
                f"- arXiv: {item['arxiv_url']}",
                f"- 发布时间: {item['published'] or '未知'}",
                f"- 更新时间: {item['updated'] or '未知'}",
                f"- 热度分数: {item['hot_score']}",
                f"- 命中查询: {', '.join(item['matched_queries']) or '无'}",
                f"- 排序来源: {', '.join(item['matched_modes']) or '无'}",
                "- 热门原因:",
            ]
        )
        lines.extend(f"  - {reason}" for reason in item["hot_reasons"])
        lines.extend(
            [
                "- 一句话摘要:",
                f"  {item['abstract'] or '无摘要'}",
                "",
            ]
        )
    if not payload["results"]:
        lines.extend(["未找到可排序的候选论文。", ""])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    args = parse_args()
    queries = normalize_queries(args.topic, args.alias)
    if not queries:
        raise SystemExit("No valid topic or aliases were provided.")
    candidates = collect_candidates(queries, per_query=args.per_query)
    payload = build_payload(args.topic, queries, candidates, top_n=args.top_n, per_query=args.per_query)
    if args.json_out:
        write_json(args.json_out, payload)
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(render_markdown(payload))
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
