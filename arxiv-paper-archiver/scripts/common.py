#!/usr/bin/env python3
"""Shared helpers for the arXiv paper archiver skill."""

from __future__ import annotations

import json
import os
import re
import subprocess
import textwrap
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import base64
import hashlib
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

ARXIV_API_URL = "https://export.arxiv.org/api/query"
BIGMODEL_LAYOUT_PARSING_URL = "https://open.bigmodel.cn/api/paas/v4/layout_parsing"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
ARXIV_MIN_DELAY_SECONDS = float(os.environ.get("ARXIV_MIN_DELAY_SECONDS", "3.5"))
ARXIV_CACHE_TTL_SECONDS = int(os.environ.get("ARXIV_CACHE_TTL_SECONDS", str(6 * 60 * 60)))
ARXIV_MAX_RETRIES = int(os.environ.get("ARXIV_MAX_RETRIES", "3"))


@dataclass
class ArxivPaper:
    arxiv_id: str
    title: str
    authors: list[str]
    published: str
    updated: str
    categories: list[str]
    abstract: str
    pdf_url: str
    entry_url: str

    def to_dict(self) -> dict:
        return asdict(self)


def iso_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def safe_mkdir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def truncate_text(value: str, limit: int) -> str:
    value = normalize_whitespace(value)
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def search_arxiv(
    query: str,
    max_results: int = 5,
    start: int = 0,
    sort_by: str = "relevance",
    sort_order: str = "descending",
) -> list[ArxivPaper]:
    search_query = build_search_query(query)
    params = {
        "search_query": search_query,
        "start": str(start),
        "max_results": str(max_results),
        "sortBy": sort_by,
        "sortOrder": sort_order,
    }
    return _run_arxiv_query(params)


def fetch_arxiv_by_id(arxiv_id: str) -> ArxivPaper | None:
    papers = _run_arxiv_query({"id_list": arxiv_id.strip()})
    return papers[0] if papers else None


def _run_arxiv_query(params: dict[str, str]) -> list[ArxivPaper]:
    payload = _load_arxiv_payload(params)
    root = ET.fromstring(payload)
    papers: list[ArxivPaper] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        paper = _parse_entry(entry)
        if paper:
            papers.append(paper)
    return papers


def _load_arxiv_payload(params: dict[str, str]) -> bytes:
    cache_path = _arxiv_cache_file(params)
    cached = _read_fresh_cache(cache_path)
    if cached is not None:
        return cached

    last_error: Exception | None = None
    for attempt in range(ARXIV_MAX_RETRIES):
        _respect_arxiv_delay()
        url = f"{ARXIV_API_URL}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(url, headers={"User-Agent": "paper-skills-arxiv-archiver/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = response.read()
            _write_bytes(cache_path, payload)
            _update_arxiv_last_request_time()
            return payload
        except urllib.error.HTTPError as exc:
            last_error = exc
            detail = exc.read().decode("utf-8", errors="ignore")
            _update_arxiv_last_request_time()
            if exc.code in {429, 500, 502, 503, 504} and attempt < ARXIV_MAX_RETRIES - 1:
                time.sleep(_retry_backoff_seconds(attempt))
                continue
            raise RuntimeError(f"arXiv API request failed: {exc.code} {detail}") from exc
        except urllib.error.URLError as exc:
            last_error = exc
            _update_arxiv_last_request_time()
            if attempt < ARXIV_MAX_RETRIES - 1:
                time.sleep(_retry_backoff_seconds(attempt))
                continue
            raise RuntimeError(f"arXiv API request failed: {exc}") from exc
    if last_error is not None:
        raise RuntimeError(f"arXiv API request failed after retries: {last_error}") from last_error
    raise RuntimeError("arXiv API request failed unexpectedly")


def _retry_backoff_seconds(attempt: int) -> float:
    return min(60.0, 10.0 * (2**attempt))


def _arxiv_cache_root() -> Path:
    configured = os.environ.get("ARXIV_CACHE_DIR")
    if configured:
        return safe_mkdir(Path(configured).expanduser())
    return safe_mkdir(Path.home() / ".cache" / "paper_skills" / "arxiv_api")


def _arxiv_cache_file(params: dict[str, str]) -> Path:
    normalized = urllib.parse.urlencode(sorted(params.items()))
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return _arxiv_cache_root() / f"{digest}.xml"


def _arxiv_state_file() -> Path:
    return _arxiv_cache_root() / "last_request.txt"


def _read_fresh_cache(path: Path) -> bytes | None:
    if not path.exists():
        return None
    age_seconds = time.time() - path.stat().st_mtime
    if age_seconds > ARXIV_CACHE_TTL_SECONDS:
        return None
    return path.read_bytes()


def _write_bytes(path: Path, payload: bytes) -> None:
    safe_mkdir(path.parent)
    path.write_bytes(payload)


def _respect_arxiv_delay() -> None:
    state_file = _arxiv_state_file()
    if not state_file.exists():
        return
    try:
        last_request = float(state_file.read_text().strip())
    except ValueError:
        return
    wait_for = ARXIV_MIN_DELAY_SECONDS - (time.time() - last_request)
    if wait_for > 0:
        time.sleep(wait_for)


def _update_arxiv_last_request_time() -> None:
    state_file = _arxiv_state_file()
    safe_mkdir(state_file.parent)
    state_file.write_text(f"{time.time():.6f}")


def build_search_query(query: str) -> str:
    tokens = [token for token in re.split(r"\s+", query.strip()) if token]
    if not tokens:
        raise ValueError("query must not be empty")
    if len(tokens) == 1:
        return f"all:{tokens[0]}"
    return " AND ".join(f"all:{token}" for token in tokens)


def _parse_entry(entry: ET.Element) -> ArxivPaper | None:
    entry_id = normalize_whitespace(entry.findtext("atom:id", default="", namespaces=ATOM_NS))
    if not entry_id:
        return None
    arxiv_id = entry_id.rsplit("/", 1)[-1]
    title = normalize_whitespace(entry.findtext("atom:title", default="", namespaces=ATOM_NS))
    abstract = normalize_whitespace(entry.findtext("atom:summary", default="", namespaces=ATOM_NS))
    published = normalize_whitespace(entry.findtext("atom:published", default="", namespaces=ATOM_NS))
    updated = normalize_whitespace(entry.findtext("atom:updated", default="", namespaces=ATOM_NS))
    authors = [
        normalize_whitespace(author.findtext("atom:name", default="", namespaces=ATOM_NS))
        for author in entry.findall("atom:author", ATOM_NS)
        if normalize_whitespace(author.findtext("atom:name", default="", namespaces=ATOM_NS))
    ]
    categories = [category.attrib.get("term", "") for category in entry.findall("atom:category", ATOM_NS)]
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    for link in entry.findall("atom:link", ATOM_NS):
        if link.attrib.get("title") == "pdf" and link.attrib.get("href"):
            pdf_url = link.attrib["href"]
            break
    return ArxivPaper(
        arxiv_id=arxiv_id,
        title=title,
        authors=authors,
        published=published,
        updated=updated,
        categories=categories,
        abstract=abstract,
        pdf_url=pdf_url,
        entry_url=entry_id,
    )


def download_file(url: str, output_path: Path) -> Path:
    request = urllib.request.Request(url, headers={"User-Agent": "paper-skills-arxiv-archiver/1.0"})
    safe_mkdir(output_path.parent)
    with urllib.request.urlopen(request, timeout=60) as response:
        output_path.write_bytes(response.read())
    return output_path


def write_json(path: Path, payload: dict | list) -> Path:
    safe_mkdir(path.parent)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return path


def read_json(path: Path) -> dict | list:
    return json.loads(path.read_text())


def extract_text_from_pdf(pdf_path: Path) -> str:
    text = _extract_with_pypdf(pdf_path)
    if text:
        return text
    return _extract_with_pdftotext(pdf_path)


def _extract_with_pypdf(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""
    try:
        reader = PdfReader(str(pdf_path))
        pages = []
        for page in reader.pages:
            extracted = page.extract_text() or ""
            if extracted.strip():
                pages.append(extracted.strip())
        return "\n\n".join(pages).strip()
    except Exception:
        return ""


def _extract_with_pdftotext(pdf_path: Path) -> str:
    try:
        result = subprocess.run(
            ["pdftotext", str(pdf_path), "-"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ""
    return result.stdout.strip()


def sanitize_filename(value: str, max_length: int = 180) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|]+", " ", value).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.rstrip(".")
    if not cleaned:
        cleaned = "paper"
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip()
    return cleaned


def pdf_filename_from_title(title: str) -> str:
    return f"{sanitize_filename(title)}.pdf"


def title_stem_from_title(title: str, fallback: str = "paper") -> str:
    cleaned = sanitize_filename(title)
    return cleaned or fallback


def markdown_filename_from_title(title: str, fallback: str = "paper") -> str:
    return f"{title_stem_from_title(title, fallback=fallback)}.md"


def archive_dirname_from_title(title: str, fallback: str = "paper") -> str:
    return title_stem_from_title(title, fallback=fallback)


def _find_existing_archive_dir(archive_dir: Path, arxiv_id: str) -> Path | None:
    legacy_dir = archive_dir / arxiv_id
    metadata_file = legacy_dir / "metadata.json"
    if metadata_file.exists():
        return legacy_dir

    for path in archive_dir.iterdir() if archive_dir.exists() else []:
        if not path.is_dir():
            continue
        candidate = path / "metadata.json"
        if not candidate.exists():
            continue
        try:
            data = read_json(candidate)
        except Exception:
            continue
        if isinstance(data, dict) and str(data.get("arxiv_id", "")).strip() == arxiv_id:
            return path
    return None


def paper_archive_dir(archive_dir: Path, arxiv_id: str, title: str | None = None) -> Path:
    if title:
        return archive_dir / archive_dirname_from_title(title, fallback=arxiv_id)
    resolved = _find_existing_archive_dir(archive_dir, arxiv_id)
    if resolved is not None:
        return resolved
    return archive_dir / arxiv_id


def metadata_path(archive_dir: Path, arxiv_id: str, title: str | None = None) -> Path:
    return paper_archive_dir(archive_dir, arxiv_id, title=title) / "metadata.json"


def pdf_path(archive_dir: Path, arxiv_id: str, title: str | None = None) -> Path:
    filename = pdf_filename_from_title(title) if title else "paper.pdf"
    return paper_archive_dir(archive_dir, arxiv_id, title=title) / filename


def extracted_text_path(archive_dir: Path, arxiv_id: str, title: str | None = None) -> Path:
    return paper_archive_dir(archive_dir, arxiv_id, title=title) / "extracted_text.md"


def load_metadata(archive_dir: Path, arxiv_id: str) -> dict:
    path = metadata_path(archive_dir, arxiv_id)
    if not path.exists():
        raise FileNotFoundError(f"metadata not found: {path}")
    data = read_json(path)
    if not isinstance(data, dict):
        raise ValueError(f"invalid metadata payload: {path}")
    return data


def load_source_text(archive_dir: Path, arxiv_id: str) -> str:
    ocr_path = ocr_markdown_path(archive_dir, arxiv_id)
    if ocr_path.exists():
        return ocr_path.read_text()
    legacy_ocr = legacy_ocr_markdown_path(archive_dir, arxiv_id)
    if legacy_ocr.exists():
        return legacy_ocr.read_text()
    path = extracted_text_path(archive_dir, arxiv_id)
    if not path.exists():
        return ""
    return path.read_text()


def ocr_markdown_path(archive_dir: Path, arxiv_id: str, title: str | None = None) -> Path:
    archive_root = paper_archive_dir(archive_dir, arxiv_id, title=title)
    if title:
        return archive_root / markdown_filename_from_title(title, fallback="ocr")
    metadata = read_json(metadata_path(archive_dir, arxiv_id))
    if isinstance(metadata, dict):
        resolved_title = str(metadata.get("title", "")).strip()
        if resolved_title:
            return archive_root / markdown_filename_from_title(resolved_title, fallback="ocr")
    return archive_root / "ocr.md"


def legacy_ocr_markdown_path(archive_dir: Path, arxiv_id: str, title: str | None = None) -> Path:
    return paper_archive_dir(archive_dir, arxiv_id, title=title) / "ocr.md"


def ocr_response_path(archive_dir: Path, arxiv_id: str, title: str | None = None) -> Path:
    return paper_archive_dir(archive_dir, arxiv_id, title=title) / "ocr_response.json"


def render_bullet_list(items: Iterable[str]) -> str:
    cleaned = [item.strip() for item in items if item and item.strip()]
    if not cleaned:
        return "- 无"
    return "\n".join(f"- {item}" for item in cleaned)


def chunk_text(value: str, max_chars: int = 8000) -> list[str]:
    value = value.strip()
    if not value:
        return []
    paragraphs = [part.strip() for part in value.split("\n\n") if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(paragraph) <= max_chars:
            current = paragraph
            continue
        wrapped = textwrap.wrap(paragraph, width=max_chars, break_long_words=False, replace_whitespace=False)
        chunks.extend(part.strip() for part in wrapped[:-1] if part.strip())
        current = wrapped[-1].strip() if wrapped else ""
    if current:
        chunks.append(current)
    return chunks


def detect_section_titles(text: str, limit: int = 8) -> list[str]:
    titles: list[str] = []
    for line in text.splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        if len(candidate) > 100:
            continue
        if re.match(r"^([0-9]+\.)+\s+", candidate) or re.match(r"^[0-9]+\s+[A-Z]", candidate):
            titles.append(candidate)
        elif candidate.isupper() and 3 <= len(candidate.split()) <= 10:
            titles.append(candidate.title())
        if len(titles) >= limit:
            break
    return titles


def resolve_title_zh(title: str) -> str:
    return f"{title}（中文整理）"


def encode_file_as_base64_data_url(path: Path) -> str:
    suffix = path.suffix.lower()
    mime_type = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }.get(suffix, "application/octet-stream")
    raw = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{raw}"


def call_glm_ocr(file_value: str, api_key: str, timeout: int = 300) -> dict:
    body = {"model": "glm-ocr", "file": file_value}
    payload_bytes = json.dumps(body).encode("utf-8")
    auth_variants = [f"Bearer {api_key}", api_key]
    last_error: Exception | None = None
    for auth_header in auth_variants:
        request = urllib.request.Request(
            BIGMODEL_LAYOUT_PARSING_URL,
            data=payload_bytes,
            headers={
                "Authorization": auth_header,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read())
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code in {401, 403}:
                continue
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"GLM-OCR request failed: {exc.code} {detail}") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("GLM-OCR returned an unexpected response")
        return payload
    if last_error is not None:
        detail = last_error.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"GLM-OCR authentication failed: {last_error.code} {detail}") from last_error
    raise RuntimeError("GLM-OCR authentication failed")


def get_bigmodel_api_key(explicit_key: str | None = None) -> str:
    key = explicit_key or os.environ.get("BIGMODEL_API_KEY") or os.environ.get("ZHIPU_API_KEY")
    if not key:
        raise RuntimeError("BIGMODEL_API_KEY is not set")
    return key


def build_paper_context(metadata: dict, source_text: str, excerpt_limit: int = 24000) -> str:
    section_titles = detect_section_titles(source_text)
    excerpt = truncate_text(source_text, excerpt_limit) if source_text else ""
    return "\n".join(
        [
            "# 论文上下文包",
            "",
            "## 元数据",
            f"- arXiv ID: {metadata.get('arxiv_id', '')}",
            f"- 标题: {metadata.get('title', '')}",
            f"- 作者: {', '.join(metadata.get('authors', [])) or '未知'}",
            f"- 发布日期: {metadata.get('published', '未知')}",
            f"- 更新日期: {metadata.get('updated', '未知')}",
            f"- 分类: {', '.join(metadata.get('categories', [])) or '未知'}",
            f"- 原始查询: {metadata.get('query', '') or '未记录'}",
            f"- 原文页面: {metadata.get('entry_url', '')}",
            f"- PDF: {metadata.get('pdf_url', '')}",
            f"- 本地 PDF: {metadata.get('files', {}).get('pdf', '') if isinstance(metadata.get('files'), dict) else ''}",
            "",
            "## arXiv Abstract",
            metadata.get("abstract", "") or "无",
            "",
            "## 识别到的章节标题",
            render_bullet_list(section_titles[:12]),
            "",
            "## 正文节选",
            excerpt or "未抽取到正文；仅可依赖 abstract 和元数据。",
            "",
        ]
    )


def compose_summary_prompt(metadata: dict, summary_output_path: Path, context_path: Path) -> str:
    return f"""
请使用你当前会话里的模型能力，根据 `{context_path}` 中的论文上下文，生成一份中文 Markdown 摘要，并写入 `{summary_output_path}`。

严格使用以下结构：

# 中文标题
中文标题内容

## 原文标题
## 论文基本信息
## 中文摘要
## 核心贡献
## 方法概述
## 实验/结果要点
## 局限性
## 适合谁读
## 原文链接

要求：
1. 优先依据正文节选；若正文不足，明确标注主要依据 arXiv abstract。
2. 内容具体，不要空话。
3. 保留 arXiv ID、作者、时间、分类、论文页链接、PDF 链接。
4. 直接写最终 Markdown 文件，不要输出过程说明。
""".strip()


def compose_translation_prompt(metadata: dict, translation_output_path: Path, context_path: Path) -> str:
    return f"""
请使用你当前会话里的模型能力，根据 `{context_path}` 中的论文上下文，生成一份中文 Markdown 全文翻译，并写入 `{translation_output_path}`。

严格使用以下结构：

# 中文标题
中文标题内容

## 标题与元数据
## 翻译说明
## 按章节翻译后的正文
## 专有名词保留策略
## 术语对照表

要求：
1. 保留公式、表格标题、引用编号、模型名、数据集名的原文。
2. 正文不足时，在“翻译说明”中明确写明这是基于可提取片段和 abstract 的不完整翻译。
3. 直接写最终 Markdown 文件，不要输出过程说明。
4. 如果上下文过长，优先翻译最重要的章节，并在“翻译说明”中说明截断范围。
""".strip()
