# ArXiv Paper Archiver 使用说明

`arxiv-paper-archiver` 是一个面向研究型工作流的 skill，用来帮助 AI 或用户完成以下任务：

- 搜索 arXiv 论文
- 发现某个方向的热门论文
- 下载并归档原始 PDF
- 调用 `GLM-OCR` 解析论文版面
- 生成中文摘要
- 生成带图的中文全文翻译
- 产出适合 VS Code / Obsidian 阅读的 Markdown 文件

这份 README 面向中文使用者，重点说明如何实际使用这套 skill。

## 1. 这个 skill 能做什么

当前主要支持这些能力：

- 按关键词或主题搜索 arXiv
- 按任意研究主题生成 Top N 热门论文榜单
- 下载原始 PDF，并按论文英文标题归档
- 通过 `GLM-OCR` 把 PDF 解析成结构化 Markdown
- 生成中文摘要的上下文包和提示词
- 生成中文全文翻译的上下文包和提示词
- 生成带图的 Markdown 阅读版

一句话概括：

它可以把一篇 arXiv 论文从“网页链接”变成“本地归档 PDF + OCR 结构化文本 + 中文摘要 + 带图中文翻译”。

## 2. 目录结构

skill 目录结构如下：

```text
arxiv-paper-archiver/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── claude_adapter.md
│   ├── error_policy.md
│   └── output_format.md
└── scripts/
    ├── archive_paper.py
    ├── common.py
    ├── find_hot_papers.py
    ├── ocr_paper.py
    ├── render_ocr_figures.py
    ├── search_arxiv.py
    ├── summarize_paper.py
    └── translate_paper.py
```

## 3. 命名规则

这套 skill 有一个非常明确的规则：

- 所有用户可见的归档和 Markdown 文件都优先按论文英文标题命名
- 不要把 `arXiv ID` 当成用户看到的归档名

当前默认命名规则是：

- 原始 PDF：
  `archive_dir/<english-title>/<english-title>.pdf`
- OCR Markdown：
  `archive_dir/<english-title>/<english-title>.md`
- 中文摘要：
  `summary_dir/<english-title>.md`
- 中文摘要上下文包：
  `summary_dir/<english-title>.context.md`
- 中文摘要提示词：
  `summary_dir/<english-title>.prompt.md`
- 中文翻译：
  `translation_dir/<english-title>.md`
- 中文翻译上下文包：
  `translation_dir/<english-title>.context.md`
- 中文翻译提示词：
  `translation_dir/<english-title>.prompt.md`
- 带图中文版：
  `rendered/<english-title>.translation.rendered.md`

`arXiv ID` 仍然保留在：

- `metadata.json`
- 检索结果
- 程序内部查找逻辑

但不应该作为用户视角下的最终归档名称。

## 4. 依赖与环境

### 4.1 Python

建议使用 `python3.12`。

### 4.2 OCR

调用 `GLM-OCR` 需要配置以下环境变量之一：

```bash
export BIGMODEL_API_KEY="你的 key"
```

或：

```bash
export ZHIPU_API_KEY="你的 key"
```

### 4.3 PDF 裁图

如果你要生成带图的 Markdown，`render_ocr_figures.py` 需要 PDF 渲染能力。

当前脚本测试时使用的是：

- `PyMuPDF`

### 4.4 arXiv API

内置了：

- 本地缓存
- 最小请求间隔
- 指数退避重试

可选环境变量：

```bash
export ARXIV_MIN_DELAY_SECONDS=3.5
export ARXIV_CACHE_TTL_SECONDS=21600
export ARXIV_MAX_RETRIES=3
```

## 5. 核心原则

### 5.1 翻译前必须先 OCR

全文翻译时，不能跳过 OCR 直接让模型“凭自己能力翻译”。

正确流程是：

1. 先归档 PDF
2. 再调用 `ocr_paper.py`
3. 然后基于 OCR 结果准备翻译上下文
4. 最后生成中文翻译

只有在 OCR 确实失败时，才允许退回到非 OCR 路径，并且必须明确说明这是降级结果。

### 5.2 中文翻译默认要带图

只要 OCR 中存在 figure placeholder 或可识别图区：

- 中文全文翻译默认必须产出带图版本
- 不能只给纯文本 Markdown

最终推荐交付：

- `rendered/<english-title>.translation.rendered.md`
- `rendered/figures/`

### 5.3 不要暴力调用 arXiv API

这套 skill 已经内置限流和缓存。

使用时应遵守：

- 不要并发打很多 arXiv 请求
- 相同 query 优先吃缓存
- 大范围抓取时不要硬刷 search API

## 6. 常见使用流程

### 6.1 搜索论文

```bash
python3.12 scripts/search_arxiv.py \
  --query "vision language model agents" \
  --max-results 5
```

### 6.2 发现热门论文

```bash
python3.12 scripts/find_hot_papers.py \
  --topic "multi agent systems for code generation" \
  --alias "code agents" \
  --alias "software engineering agents" \
  --top-n 10 \
  --json-out /tmp/papers/hot/2026-04-05/hot_papers.json \
  --md-out /tmp/papers/hot/2026-04-05/hot_papers.md
```

### 6.3 归档 PDF

```bash
python3.12 scripts/archive_paper.py \
  --arxiv-id 2401.01234 \
  --query "vision language model agents" \
  --archive-dir /tmp/papers/archive
```

### 6.4 运行 OCR

```bash
python3.12 scripts/ocr_paper.py \
  --arxiv-id 2401.01234 \
  --archive-dir /tmp/papers/archive
```

### 6.5 准备中文摘要上下文包

```bash
python3.12 scripts/summarize_paper.py \
  --arxiv-id 2401.01234 \
  --archive-dir /tmp/papers/archive \
  --summary-dir /tmp/papers/summaries
```

### 6.6 准备中文翻译上下文包

```bash
python3.12 scripts/translate_paper.py \
  --arxiv-id 2401.01234 \
  --archive-dir /tmp/papers/archive \
  --translation-dir /tmp/papers/translations
```

### 6.7 生成带图 Markdown

```bash
python3.12 scripts/render_ocr_figures.py \
  --pdf "/tmp/papers/archive/Example Paper Title/Example Paper Title.pdf" \
  --ocr-md "/tmp/papers/archive/Example Paper Title/Example Paper Title.md" \
  --ocr-response-json "/tmp/papers/archive/Example Paper Title/ocr_response.json" \
  --output-dir /tmp/papers/rendered
```

## 7. Claude Code 怎么接入

这套 skill 已经支持 Claude Code。

推荐方式是：

- 把它当作“脚本工具包 + 工作流规范”来用
- 让 Claude Code 调用 `scripts/` 下的脚本
- 再由 Claude Code 当前会话模型生成最终中文文件

具体说明见：

- [SKILL.md](./SKILL.md)
- [references/claude_adapter.md](./references/claude_adapter.md)

Claude Code 工作流建议：

1. 搜索或发现热门论文
2. 归档 PDF
3. 先做 OCR
4. 再做摘要或翻译
5. 中文翻译完成后生成带图 Markdown

## 8. Codex 怎么接入

这套 skill 也支持 Codex / Codex Desktop。

相关元数据在：

- [agents/openai.yaml](./agents/openai.yaml)

Codex 应该优先遵循：

- [SKILL.md](./SKILL.md)

## 9. 主要脚本说明

### `search_arxiv.py`

按主题或关键词搜索 arXiv，返回标准化结果。

### `find_hot_papers.py`

针对任意研究主题找 Top N 热门论文。

### `archive_paper.py`

下载论文 PDF，并按英文论文标题归档。

### `ocr_paper.py`

调用 `GLM-OCR`，把归档后的 PDF 解析成结构化 Markdown。

### `summarize_paper.py`

生成中文摘要所需的：

- `.context.md`
- `.prompt.md`

### `translate_paper.py`

生成中文全文翻译所需的：

- `.context.md`
- `.prompt.md`

### `render_ocr_figures.py`

把 OCR 中的图像占位替换成真实图片，方便 Markdown 渲染。

## 10. 推荐交付物

如果你要把论文真正交付给人阅读，我推荐保留这几类文件：

- 原始 PDF
- `metadata.json`
- OCR Markdown
- 中文摘要 Markdown
- 带图中文全文 Markdown
- `figures/`

## 11. 注意事项

- 不要让模型跳过 OCR 直接翻全文
- 不要把 `arXiv ID` 当成用户可见文件名
- 不要只输出纯文本中文版而忽略图表
- 不要对 arXiv API 做高频并发请求

## 12. 相关文档

- [SKILL.md](./SKILL.md)
- [references/claude_adapter.md](./references/claude_adapter.md)
- [references/output_format.md](./references/output_format.md)
- [references/error_policy.md](./references/error_policy.md)
