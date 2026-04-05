# ArXiv Paper Archiver

把 arXiv 论文一键整理成适合中文阅读、知识归档和 AI 工作流的研究资料。

主要能力：

- 搜索论文
- 发现某个方向的热门论文
- 下载原始 PDF
- 调用 `GLM-OCR` 做版面解析
- 生成中文摘要
- 生成带图的中文全文翻译
- 输出可归档、可阅读、可二次加工的 Markdown 文件

## 基于GLM ORC的文本翻译能力

- 输入：一篇英文 PDF
- 输出：一份带图的中文 Markdown

示例论文：

- `Attention Is All You Need`

输入文件：

```text
demo/attention-is-all-you-need/
└── Attention Is All You Need.pdf
```

输出文件：

```text
demo/attention-is-all-you-need/
├── Attention Is All You Need.translation.rendered.md
└── figures/
    ├── figure-01-page-3.png
    ├── figure-02-page-4.png
    ├── figure-03-page-13.png
    ├── figure-04-page-14.png
    └── figure-05-page-15.png
```

完整翻译文档：
- [demo/attention-is-all-you-need/Attention Is All You Need.translation.rendered.md](./demo/attention-is-all-you-need/Attention%20Is%20All%20You%20Need.translation.rendered.md)

## Demo

输入一句话：

```text
找最近一周最热门的 AI agents 论文，下载 PDF，翻译成中文并保留图表。
```

你最终可以得到：

```text
demo/attention-is-all-you-need/
├── Attention Is All You Need.pdf
├── Attention Is All You Need.translation.rendered.md
└── figures/
```

也就是说，它会把“论文链接”变成：

- 原始 PDF
- 带图中文全文
- 可直接放进知识库的 Markdown 产物

## 工作流特性

- 默认按英文论文标题命名 PDF、OCR Markdown、摘要和翻译文件
- 全文翻译前默认先跑 `GLM-OCR`
- 中文全文翻译默认保留图表
- 支持输出带图的 Markdown，适合 VS Code 和 Obsidian
- 同时支持 Codex skill 和 Claude Code 脚本工作流

## 核心能力

当前支持：

- 按关键词或主题搜索 arXiv
- 按任意研究方向生成 Top N 热门论文榜单
- 下载并按论文标题归档 PDF
- 调用 `GLM-OCR` 输出结构化 Markdown
- 生成中文摘要上下文包
- 生成中文全文翻译上下文包
- 生成带图的可渲染 Markdown 版本

## 快速开始

下面假设你已经进入：

```bash
cd arxiv-paper-archiver
```

### 1. 配置 OCR API Key

配置以下任意一个环境变量即可：

```bash
export BIGMODEL_API_KEY="你的 key"
```

或者：

```bash
export ZHIPU_API_KEY="你的 key"
```

### 2. 搜索论文

```bash
python3.12 scripts/search_arxiv.py \
  --query "vision language model agents" \
  --max-results 5
```

### 3. 归档 PDF

```bash
python3.12 scripts/archive_paper.py \
  --arxiv-id 2401.01234 \
  --query "vision language model agents" \
  --archive-dir /tmp/papers/archive
```

### 4. 先做 OCR，再做翻译

```bash
python3.12 scripts/ocr_paper.py \
  --arxiv-id 2401.01234 \
  --archive-dir /tmp/papers/archive
```

```bash
python3.12 scripts/translate_paper.py \
  --arxiv-id 2401.01234 \
  --archive-dir /tmp/papers/archive \
  --translation-dir /tmp/papers/translations
```

### 5. 生成带图版 Markdown

```bash
python3.12 scripts/render_ocr_figures.py \
  --pdf "/tmp/papers/archive/Example Paper Title/Example Paper Title.pdf" \
  --ocr-md "/tmp/papers/archive/Example Paper Title/Example Paper Title.md" \
  --ocr-response-json "/tmp/papers/archive/Example Paper Title/ocr_response.json" \
  --output-dir /tmp/papers/rendered
```

## 默认规则

这个 skill 有一些强约束，不是可选建议：

### 命名规则

- 原始 PDF 按英文论文标题命名
- OCR Markdown 按英文论文标题命名
- 中文摘要按英文论文标题命名
- 中文翻译按英文论文标题命名
- 不把 `arXiv ID` 当成用户可见文件名

### 翻译规则

- 全文翻译前必须先跑 `ocr_paper.py`
- 不要跳过 OCR 直接让模型自己翻整篇论文
- 默认应输出完整翻译，不应只翻译部分章节或只给压缩版概述
- OCR 失败时才能走降级路径

### 图表规则

- 中文全文翻译默认要保留图表
- 能识别 figure 时，要输出带图版 Markdown

### arXiv API 规则

- 内置缓存
- 内置限流
- 内置重试
- 不建议高频并发搜索

## 热门论文发现

除了普通搜索，这个 skill 还支持：

- 给一个研究方向
- 自动输出 Top N 热门论文榜单

示例：

```bash
python3.12 scripts/find_hot_papers.py \
  --topic "multi agent systems for code generation" \
  --alias "code agents" \
  --alias "software engineering agents" \
  --top-n 10 \
  --json-out /tmp/papers/hot/2026-04-05/hot_papers.json \
  --md-out /tmp/papers/hot/2026-04-05/hot_papers.md
```

这个功能适合：

- 做 weekly paper review
- 跟踪某个细分方向
- 让 AI 自动先帮你筛论文

## Claude Code 怎么接入

这套 skill 已经能直接作为 Claude Code 的工作流后端使用。

推荐方式：

- 让 Claude Code 调用 `scripts/` 下的脚本
- 让 Claude Code 当前会话模型负责最终中文生成
- 把输出目录直接指向你的本地知识库、项目目录或 Obsidian Vault

重点约束：

- 全文翻译前必须先 OCR
- 中文翻译默认保留图表
- 用户看到的文件统一按英文论文标题命名

详细说明见：

- [SKILL.md](./arxiv-paper-archiver/SKILL.md)
- [references/claude_adapter.md](./arxiv-paper-archiver/references/claude_adapter.md)

## Codex 怎么接入

这套 skill 也支持 Codex / Codex Desktop。

相关文件：

- [SKILL.md](./arxiv-paper-archiver/SKILL.md)
- [agents/openai.yaml](./arxiv-paper-archiver/agents/openai.yaml)

## 仓库结构

```text
paper_skills/
├── README.md
└── arxiv-paper-archiver/
    ├── SKILL.md
    ├── agents/
    ├── references/
    └── scripts/
```

## 主要脚本

- `search_arxiv.py`: 搜索 arXiv
- `find_hot_papers.py`: 找热门论文
- `archive_paper.py`: 下载并归档 PDF
- `ocr_paper.py`: 调用 `GLM-OCR`
- `summarize_paper.py`: 生成摘要上下文包
- `translate_paper.py`: 生成翻译上下文包
- `render_ocr_figures.py`: 生成带图 Markdown

## 相关文档

- [SKILL.md](./arxiv-paper-archiver/SKILL.md)
- [references/claude_adapter.md](./arxiv-paper-archiver/references/claude_adapter.md)
- [references/output_format.md](./arxiv-paper-archiver/references/output_format.md)
- [references/error_policy.md](./arxiv-paper-archiver/references/error_policy.md)
