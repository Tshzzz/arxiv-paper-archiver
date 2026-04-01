# Output Format

## Metadata JSON

Store metadata at `archive_dir/<arxiv_id>/metadata.json`.

Required fields:

- `arxiv_id`
- `title`
- `authors`
- `published`
- `updated`
- `categories`
- `abstract`
- `pdf_url`
- `query`
- `downloaded_at`

Recommended extra fields:

- `entry_url`
- `archive_dir`
- `files`
- `extraction_status`

## Archived Files

Store archived source files under `archive_dir/<arxiv_id>/`.

This `arxiv_id` path is an internal storage key for deduplication and lookup. User-facing archive naming should still follow the paper's English title.

- `<english-title>.pdf`: downloaded PDF from arXiv using the paper's English title as the filename
- `metadata.json`: normalized metadata and provenance
- `extracted_text.md`: extracted paper text, if PDF text extraction succeeds
- `ocr.md`: GLM-OCR markdown output, preferred when present
- `ocr_response.json`: raw GLM-OCR API response for debugging and audit

## Hot Papers Report

Store hot-paper reports at `hot_dir/YYYY-MM-DD/`.

- `hot_papers.json`: machine-readable ranked results
- `hot_papers.md`: human-readable Top N report

`hot_papers.json` should include at least:

- `generated_at`
- `topic`
- `queries_used`
- `top_n`
- `candidate_count`
- `scoring_method`
- `results`

Each result should include at least:

- `rank`
- `title`
- `arxiv_id`
- `arxiv_url`
- `pdf_url`
- `published`
- `updated`
- `authors`
- `categories`
- `abstract`
- `hot_score`
- `hot_reasons`
- `matched_queries`
- `matched_modes`
- `evidence`
- `scores`

Recommended retention policy:

- Keep the original archive primarily as the title-named PDF.
- Treat the title-named PDF as the user-facing archive name. The `arxiv_id` should remain metadata, not the visible archive label.
- Treat `metadata.json`, `extracted_text.md`, `ocr.md`, and `ocr_response.json` as rebuildable workflow artifacts.

## Chinese Summary Markdown

Store summaries at `summary_dir/<arxiv_id>.md`.
Optional prep artifacts:

- `summary_dir/<arxiv_id>.context.md`
- `summary_dir/<arxiv_id>.prompt.md`

Use this exact section order:

1. `# 中文标题`
2. `## 原文标题`
3. `## 论文基本信息`
4. `## 中文摘要`
5. `## 核心贡献`
6. `## 方法概述`
7. `## 实验/结果要点`
8. `## 局限性`
9. `## 适合谁读`
10. `## 原文链接`

## Chinese Full Translation Markdown

Store translations at `translation_dir/<english-title>.md`.
Optional prep artifacts:

- `translation_dir/<english-title>.context.md`
- `translation_dir/<english-title>.prompt.md`
- `rendered/figures/*.png`
- `rendered/<english-title>.translation.rendered.md`

Recommended retention policy:

- Keep the Chinese reading version as the figure-backed translation Markdown plus the corresponding figures directory.
- Treat `rendered/<english-title>.translation.rendered.md` as the preferred final delivery file when OCR figure placeholders are available.

Use this exact section order:

1. `# 中文标题`
2. `## 标题与元数据`
3. `## 翻译说明`
4. `## 按章节翻译后的正文`
5. `## 专有名词保留策略`
6. `## 术语对照表`

If translation is interrupted, keep the partial file and add a clear note under `## 翻译说明`.

Figure requirement:

- A Chinese full translation should preserve paper figures and charts whenever OCR output contains figure placeholders or detectable figure regions.
- The final translation handoff should include both the English-title Markdown file and the `figures/` directory needed to render inline images.
- Do not present the translation deliverable to users as an `arXiv ID`-named file.
