# Claude Code Adapter

Use this skill in Claude Code as a lightweight workflow wrapper around the bundled scripts.

## Expected User Requests

- “帮我找一下某个方向最新的 arXiv 论文，并归档下来。”
- “把这个研究方向最热的 top 10 论文找出来。”
- “我给你一个问题，你帮我找这个领域最热门的论文。”
- “搜索 diffusion transformer 相关 arXiv 论文，下载 PDF，总结成中文。”
- “把这篇 arXiv 论文存档，并翻译成中文放到另一个目录。”

## Recommended Workflow

1. If the user asks for “最热”, “top N”, or gives only a broad research problem, first normalize it into 2-5 focused English aliases.
2. Run `scripts/find_hot_papers.py` with `--topic`, repeated `--alias`, and `--top-n`.
3. If the user only wants plain arXiv search results instead of a hot list, run `scripts/search_arxiv.py` with `--query` and `--max-results`.
4. Trust the built-in cache and rate limiter; do not fan out concurrent manual arXiv search loops around the scripts.
5. Pick one paper from the JSON results.
6. Run `scripts/archive_paper.py` with `--arxiv-id`, `--query`, and `--archive-dir`.
7. If the PDF is layout-heavy, run `scripts/ocr_paper.py` so downstream steps can use `ocr.md`.
8. Read `ocr.md` when present, otherwise read `metadata.json` and `extracted_text.md`, then use the current Claude Code session model to write the final Chinese summary.
9. Read the same archive files and use the current Claude Code session model to write the final Chinese translation only when requested.
10. When writing a Chinese full translation, treat the figure-backed Markdown version as the default deliverable. If OCR figure placeholders exist, run `scripts/render_ocr_figures.py` and keep the paired `figures/` directory.
11. If you want a reusable handoff artifact for another workflow, run `scripts/summarize_paper.py` or `scripts/translate_paper.py` to prepare `.prompt.md` and `.context.md` files.

## Example Commands

```bash
python3 scripts/search_arxiv.py \
  --query "diffusion transformer" \
  --max-results 5
```

```bash
python3 scripts/find_hot_papers.py \
  --topic "code agents for software engineering" \
  --alias "code agents" \
  --alias "software engineering agents" \
  --alias "LLM coding agents" \
  --top-n 10 \
  --json-out /tmp/papers/hot/2026-04-01/hot_papers.json \
  --md-out /tmp/papers/hot/2026-04-01/hot_papers.md
```

```bash
python3 scripts/archive_paper.py \
  --arxiv-id 2401.01234 \
  --query "diffusion transformer" \
  --archive-dir /tmp/papers/archive
```

```bash
python3 scripts/ocr_paper.py \
  --arxiv-id 2401.01234 \
  --archive-dir /tmp/papers/archive
```

```bash
python3 scripts/summarize_paper.py \
  --arxiv-id 2401.01234 \
  --archive-dir /tmp/papers/archive \
  --summary-dir /tmp/papers/summaries
```

```bash
python3 scripts/translate_paper.py \
  --arxiv-id 2401.01234 \
  --archive-dir /tmp/papers/archive \
  --translation-dir /tmp/papers/translations
```

After generating the `.prompt.md` and `.context.md` files, Claude Code can read them and write the final `.md` output using the current session model. No separate API key is required for that step.

For GLM-OCR, configure one of:

- `BIGMODEL_API_KEY`
- `ZHIPU_API_KEY`

`ocr_paper.py` defaults to sending the archived local PDF as `base64`, which is supported by the official layout parsing API. You can also use `--file-mode url` to send `metadata.pdf_url`.

For arXiv search behavior:

- The scripts cache repeated identical queries locally.
- Uncached arXiv calls are rate-limited to a polite interval.
- If you need large-scale harvesting, do not simulate it with many search calls; switch workflows instead.

## Output Contract

- Hot-paper reports go under `hot_dir/YYYY-MM-DD/`
- Use `find_hot_papers.py` when you need a ranked list rather than a plain relevance search
- Archive files go under `archive_dir/<arxiv_id>/` for internal lookup only
- The original PDF should use the paper's English title as the filename.
- When describing or organizing archives for the user, refer to the paper by its title-based archive name rather than by the arXiv ID.
- OCR markdown goes to `archive_dir/<arxiv_id>/ocr.md`
- Final summaries go to `summary_dir/<arxiv_id>.md`
- Final translations go to `translation_dir/<english-title>.md`
- Preferred final reading translations go to `rendered/<english-title>.translation.rendered.md`
- Figure assets for Chinese translations go to `rendered/figures/`
- Optional prep artifacts go to `*.context.md` and `*.prompt.md`

User-facing naming rule:

- Use English paper titles for archive names and Chinese translation filenames.
- Keep `arXiv ID` only for internal lookup, provenance, and metadata.

Preferred retention model:

- Keep the original source paper as the English-title PDF.
- Keep the Chinese deliverable as a figure-backed Markdown file named by the paper's English title plus `figures/`.

Avoid duplicating logic in prompts. Let the scripts own the normalization, file layout, and output format.
