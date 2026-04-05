---
name: arxiv-paper-archiver
description: Search arXiv by topic or keyword, discover top-N hot papers for an arbitrary research topic, download and archive paper PDFs with metadata, run GLM-OCR for layout-aware parsing, prepare Chinese summary and translation context packets, and render OCR figures into Markdown-friendly image assets. Use when Codex needs to find arXiv papers, rank hot papers for a topic, build a local paper archive, extract structured paper content from PDFs, summarize research papers in Chinese, prepare full-paper Chinese translations, or generate Markdown documents with figures that also work in Claude Code or note-taking workflows.
---

# ArXiv Paper Archiver

Archive arXiv papers into a stable local directory layout, keep the original PDF using the paper's English title as the filename, and treat the paper title as the archive name from the user's point of view rather than using the arXiv ID as the visible archive label. Run GLM-OCR on the archived PDF before paper translation work so the agent works from a structured document source instead of translating from its own memory or rough PDF text extraction. Discover the hottest papers for a research topic, then use the current Claude Code or Codex session model to generate a Chinese summary and an optional full Chinese translation. Chinese translations must include the paper's figures and charts as renderable Markdown assets whenever OCR placeholders or figure regions are available. Use the bundled scripts for search, hot-paper discovery, archive, OCR, and prompt/context preparation.

## Core Capabilities

This skill gives the current AI agent a reusable paper-processing workflow with these capabilities:

- Search arXiv by topic or keyword and return normalized paper candidates.
- Find top-N hot papers for an arbitrary topic by combining multi-query consensus, ranking position, recency, and topic relevance.
- Archive a selected paper locally with stable filenames and metadata for later reuse.
- Keep the original paper PDF under the archive folder using the paper's English title as the filename.
- Present archived papers to users by paper title, not by arXiv ID.
- Run GLM-OCR on the archived PDF so the agent can work from layout-aware Markdown instead of plain text extraction.
- Require OCR as the default prerequisite for full-paper translation; do not rely on the model to freestyle or reconstruct the paper directly from the raw PDF or from memory.
- Prepare `.context.md` and `.prompt.md` packets so the current Claude Code or Codex session can write high-quality Chinese summaries and translations without embedding all workflow logic in the prompt.
- Prefer OCR output over plain extracted text when generating downstream summary or translation context.
- Render OCR figure placeholders into real PNG assets and a Markdown copy that VS Code or Obsidian can preview with inline images.
- Treat figure-backed Chinese translation output as the default translation deliverable, not an optional extra.
- Rate-limit and cache arXiv API queries so repeated lookups do not hammer the API.
- Support both Codex Skill usage and Claude Code script-toolkit usage with the same directory layout.

When another AI uses this skill correctly, it should be able to turn an arXiv paper into:

- a local paper archive,
- a ranked hot-paper list for any research topic,
- an English-title PDF for the original paper,
- a layout-aware OCR Markdown source,
- a Chinese summary handoff packet,
- a Chinese translation handoff packet,
- a figure-rendered Chinese translation Markdown artifact,
- and a figure-rendered Markdown artifact suitable for reading in editors.

## Quick Start

Run the workflow in this order:

1. Search papers with `scripts/search_arxiv.py`, or find a hot list with `scripts/find_hot_papers.py`.
2. Pick an `arxiv_id` from the results.
3. Archive the paper with `scripts/archive_paper.py`.
4. Before translating a paper, run `scripts/ocr_paper.py` on the archived PDF so the translation is grounded in OCR output.
5. Generate the Chinese summary with the current session model, or run `scripts/summarize_paper.py` to prepare a prompt/context packet first.
6. Generate the full Chinese translation with the current session model, or run `scripts/translate_paper.py` to prepare a prompt/context packet first.
7. For every Chinese full translation, run `scripts/render_ocr_figures.py` whenever OCR figure placeholders are available, then produce a figure-backed Markdown translation that references the generated `figures/` assets.
8. When you need editor-friendly figure rendering for the OCR source itself, run `scripts/render_ocr_figures.py` to replace OCR figure placeholders with real PNG files and a Markdown copy.

Example:

```bash
python3 scripts/search_arxiv.py \
  --query "vision language model agents" \
  --max-results 5

python3 scripts/find_hot_papers.py \
  --topic "multi agent systems for code generation" \
  --alias "code agents" \
  --alias "software engineering agents" \
  --top-n 10 \
  --json-out /tmp/papers/hot/2026-04-01/hot_papers.json \
  --md-out /tmp/papers/hot/2026-04-01/hot_papers.md

python3 scripts/archive_paper.py \
  --arxiv-id 2401.01234 \
  --query "vision language model agents" \
  --archive-dir /tmp/papers/archive

python3 scripts/ocr_paper.py \
  --arxiv-id 2401.01234 \
  --archive-dir /tmp/papers/archive

python3 scripts/summarize_paper.py \
  --arxiv-id 2401.01234 \
  --archive-dir /tmp/papers/archive \
  --summary-dir /tmp/papers/summaries

python3 scripts/translate_paper.py \
  --arxiv-id 2401.01234 \
  --archive-dir /tmp/papers/archive \
  --translation-dir /tmp/papers/translations

/tmp/papers/venv-pdf/bin/python scripts/render_ocr_figures.py \
  --pdf "/tmp/papers/archive/2401.01234/Example Paper Title.pdf" \
  --ocr-md "/tmp/papers/archive/Example Paper Title/Example Paper Title.md" \
  --ocr-response-json /tmp/papers/archive/2401.01234/ocr_response.json \
  --output-dir /tmp/papers/rendered
```

## Workflow Rules

Use the scripts instead of reimplementing the pipeline in prompts or ad hoc shell glue.

- Search first. Do not guess paper IDs from titles unless the user already provided one.
- When the user asks for “top papers”, “today's hottest papers”, or “这个方向最值得看的论文”, prefer `scripts/find_hot_papers.py` instead of plain search.
- When the user's topic is in Chinese or phrased as a natural-language question, first normalize it into 2-5 concise English query aliases before calling `scripts/find_hot_papers.py`.
- Respect arXiv API politeness rules: keep one request stream, wait at least about 3 seconds between uncached requests, and prefer cache hits over repeated identical queries.
- For large result sets, refine the query or request smaller slices instead of paging aggressively through thousands of results.
- Archive before summarizing or translating so metadata and extracted text live in a predictable location.
- Do not translate a paper by relying on the model's own background knowledge or by asking it to infer missing structure from the PDF alone.
- When referring to an archived paper in messages, file organization guidance, or downstream notes, use the paper title as the archive name; treat the arXiv ID as metadata only.
- Treat the original archive as “keep the source PDF”; treat the Chinese output as “keep Markdown plus figures”.
- Full-paper translation should call `scripts/ocr_paper.py` first. Only fall back to non-OCR inputs when OCR genuinely fails.
- Chinese full translations must preserve paper figures and charts whenever the OCR output contains figure placeholders or figure regions.
- Prefer running `scripts/render_ocr_figures.py` before finalizing any Chinese full translation, not only when the user explicitly asks for a VS Code or Obsidian friendly version.
- Always create the Chinese summary.
- Only create the full translation when the user explicitly asks for it or asks for a Chinese full-text version.
- Prefer generating the final Chinese files directly with the current Claude Code or Codex session model.
- Use `scripts/summarize_paper.py` and `scripts/translate_paper.py` when you want a reusable prompt/context packet for another agent, automation, or Obsidian shell workflow.

## Input and Output Contract

Core inputs across the workflow:

- `query`: topic or keyword query
- `topic`: free-form research topic for hot-paper discovery
- `alias`: optional English query alias for hot-paper discovery; repeatable
- `max_results`: number of search results, default `5`
- `top_n`: number of hot papers to return, default `10`
- `archive_dir`: root directory for PDFs and metadata
- `summary_dir`: output directory for Chinese summaries
- `translation_dir`: output directory for Chinese translations
Internal storage layout:

- `archive_dir/<english-title>/<english-title>.pdf`
- `archive_dir/<english-title>/metadata.json`
- `archive_dir/<english-title>/extracted_text.md`
- `archive_dir/<english-title>/<english-title>.md`
- `archive_dir/<english-title>/ocr_response.json`
- `hot_dir/YYYY-MM-DD/hot_papers.json`
- `hot_dir/YYYY-MM-DD/hot_papers.md`
- `summary_dir/<arxiv_id>.md`
- `translation_dir/<english-title>.md`
- `summary_dir/<arxiv_id>.context.md`
- `summary_dir/<arxiv_id>.prompt.md`
- `translation_dir/<english-title>.context.md`
- `translation_dir/<english-title>.prompt.md`
- `rendered/figures/*.png`
- `rendered/ocr.rendered.md`
- `rendered/<english-title>.translation.rendered.md`

User-facing naming rule:

- Archive the source paper by its English paper title, not by arXiv ID.
- Save Chinese full translations by the English paper title, not by arXiv ID.
- Treat `arXiv ID` as an internal lookup key and metadata field unless the user explicitly asks for it.
- New archives should not create `archive_dir/<arxiv_id>/...` folders.

Practical retention rule:

- Keep the original paper as the English-title PDF, and treat that title-based file as the primary archive name.
- Keep the Chinese reading version as a figure-backed Markdown file named by the paper's English title plus its corresponding `figures/` directory.
- Treat `metadata.json`, `ocr_response.json`, `.context.md`, and `.prompt.md` as workflow artifacts that can be regenerated when needed.

Read [output_format.md](references/output_format.md) when you need the exact JSON fields or Markdown section order.

## arXiv API Discipline

The bundled scripts should behave politely toward the arXiv API:

- Reuse cached responses for repeated identical queries.
- Avoid concurrent bursts against `export.arxiv.org`.
- Keep uncached calls spaced by at least roughly 3 seconds.
- Prefer focused queries and modest page sizes over broad repeated scans.
- If you need bulk harvesting rather than interactive search, use a more suitable bulk interface such as OAI-PMH instead of overusing the search API.

## Script Reference

### `scripts/search_arxiv.py`

Search arXiv and print normalized JSON.

Required:

- `--query`

Optional:

- `--max-results`
- `--json-out`

### `scripts/find_hot_papers.py`

Find top-N hot papers for an arbitrary topic. This script works best when the current agent first converts the user's intent into a few focused English aliases.

Required:

- `--topic`

Optional:

- `--alias`
- `--top-n`
- `--per-query`
- `--json-out`
- `--md-out`

### `scripts/archive_paper.py`

Download the paper PDF, store it using the English paper title as the filename, write metadata, and extract source text if possible.

Required:

- `--arxiv-id`
- `--archive-dir`

Optional:

- `--query`

### `scripts/summarize_paper.py`

Prepare a summary context packet and prompt for the current agent model to write the final Chinese summary. This script prefers `ocr.md` when present and falls back to `extracted_text.md`.

Required:

- `--arxiv-id`
- `--archive-dir`
- `--summary-dir`

### `scripts/translate_paper.py`

Prepare a translation context packet and prompt for the current agent model to write the final Chinese translation. This script prefers `ocr.md` when present and falls back to `extracted_text.md`. The final translation deliverable should be a figure-backed Markdown file named by the paper's English title when figure placeholders are available.

Required:

- `--arxiv-id`
- `--archive-dir`
- `--translation-dir`

### `scripts/ocr_paper.py`

Run GLM-OCR on the archived PDF and save the OCR markdown for downstream summary and translation. The OCR Markdown file should use the paper's English title as the filename.

Required:

- `--arxiv-id`
- `--archive-dir`

Optional:

- `--api-key`
- `--file-mode`

### `scripts/render_ocr_figures.py`

Render OCR figure placeholders into real PNG assets and a Markdown copy with editor-friendly image references.

Required:

- `--pdf`
- `--ocr-md`
- `--output-dir`

Optional:

- `--ocr-response-json`
- `--ocr-page-width`
- `--ocr-page-height`
- `--zoom`

Use this script when the user says:

- “图片在 Markdown 里看不见”
- “我要在 VS Code/Obsidian 里看带图版本”
- “把 OCR 里的 figure 占位替换成真实图片”

When producing a Chinese full translation:

- Run this script by default if OCR output contains figure placeholders.
- Save the final reading copy as `rendered/<english-title>.translation.rendered.md`.
- Keep the paired `rendered/figures/` directory as part of the translation deliverable.

Use `scripts/find_hot_papers.py` when the user says:

- “把今天这个方向最热的论文找出来”
- “给我这个领域 top 10 最热门的论文”
- “我只知道研究问题，不知道该搜什么关键词”

## Text Extraction and Fallbacks

PDF text extraction is best-effort, and GLM-OCR is the preferred high-fidelity path.

- Prefer the title-named OCR Markdown file when available.
- Otherwise use `extracted_text.md` from local PDF parsing.
- If both OCR and extraction fail, generate summary and translation from metadata plus arXiv abstract, and clearly say so in the output.
- No separate API key is required for summary or translation when the current Claude Code or Codex session model is doing the writing.
- GLM-OCR requires `BIGMODEL_API_KEY` or `ZHIPU_API_KEY`.
- Figure rendering requires a PDF rasterization backend. In this repository, `scripts/render_ocr_figures.py` is tested with PyMuPDF.

## Decision Guide

Use this decision guide so the AI knows which ability to invoke:

- If the user wants paper discovery: run `scripts/search_arxiv.py`.
- If the user already knows the paper ID and wants a local copy: run `scripts/archive_paper.py`.
- If the user wants better handling of figures, tables, formulas, or multi-column papers: run `scripts/ocr_paper.py`.
- If the user wants a Chinese summary or translation and the current session model will do the writing: run `scripts/summarize_paper.py` or `scripts/translate_paper.py`, then use the generated `.context.md` and `.prompt.md`.
- If the user wants Markdown that displays figures correctly in editors: run `scripts/render_ocr_figures.py`.
- If the user wants a full paper workflow: search, archive, OCR, prepare summary/translation context, then optionally render figures.

Read [error_policy.md](references/error_policy.md) for failure handling and rerun behavior.

## Claude Code Compatibility

This skill is designed so Codex and Claude Code can share the same scripts and directory layout.

- Codex should use this `SKILL.md` plus `agents/openai.yaml`, then write the final Chinese files with the current session model.
- Claude Code should treat the skill as a script toolkit and follow [claude_adapter.md](references/claude_adapter.md), also using the current session model for the final Chinese files.

Keep compatibility thin. If behavior changes, update the scripts first and the adapter docs second.
