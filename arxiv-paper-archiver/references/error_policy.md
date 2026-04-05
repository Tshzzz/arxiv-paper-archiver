# Error Policy

## Search Failures

- If the arXiv API returns zero results, report that clearly and do not create empty archive directories.
- If the query is too broad, narrow it with one or two added keywords instead of silently changing the topic.
- If hot-paper discovery returns weak or noisy results, keep the original topic but refine the English aliases and rerun instead of pretending the first ranking is authoritative.
- If the user provides a Chinese or natural-language research question, normalize it into concise English search aliases before using hot-paper discovery.
- If arXiv responds with transient failures, throttling, or connectivity errors, retry with exponential backoff instead of hammering the API.
- Prefer cached responses for repeated identical queries. Do not bypass the cache with manual retry loops unless the user explicitly needs a fresh fetch.
- If a task would require broad harvesting across thousands of records, stop and switch to a more suitable bulk interface rather than flooding the search API.

## Download Failures

- If PDF download fails, stop the archive step and report the arXiv ID and failing URL.
- Do not write a fake PDF placeholder.
- Metadata may still be written only if it is useful for debugging, but must not claim the PDF exists.

## Text Extraction Failures

- If PDF text extraction fails, set `extraction_status` to `abstract_only`.
- Continue summary generation based on arXiv metadata and abstract.
- Translation should either use extracted fragments or explicitly mark the output as incomplete and abstract-based.
- Do not compensate for missing OCR by pretending the model can faithfully reconstruct the whole paper on its own.

## OCR Failures

- If GLM-OCR fails, keep the archived PDF and existing metadata.
- Store no partial title-named OCR Markdown file; only write it when `md_results` is present.
- Fall back to local PDF extraction and clearly note the degraded path in the final summary or translation if quality is affected.
- If the API rejects the file size or page count, report the actual PDF size/page count and skip OCR.

## Agent Generation Failures

- If the current agent cannot finish the Chinese summary or translation in one pass, keep the prepared `.prompt.md` and `.context.md` files so the task can be retried.
- If the current agent context window is too small for the extracted text, translate the most important sections first and say which sections were skipped.
- Do not claim a file is a full translation if it only covers fragments.
- A shortened translation is a degraded fallback only, not normal behavior for a requested paper translation.

## Idempotency

- Re-running archive should not re-download a PDF that already exists.
- Re-running summary or translation may overwrite the existing Markdown file with a newer version.
- Never delete prior archive folders automatically.
