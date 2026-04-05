# PDF -> 中文 Markdown Demo

这个 demo 用来展示这套 skill 最直观的一项能力：

- 输入一篇英文论文 PDF
- 输出一份适合 VS Code / Obsidian 阅读的带图中文 Markdown

## 示例论文

- 论文标题：`An Empirical Study of Multi-Agent Collaboration for Automated Research`
- 论文来源：arXiv
- 方向：AI agents / multi-agent systems / automated research

## 输入

归档目录中的原始 PDF：

```text
archive/
└── An Empirical Study of Multi-Agent Collaboration for Automated Research/
    └── An Empirical Study of Multi-Agent Collaboration for Automated Research.pdf
```

## 输出

最终交付物不是纯文本，而是：

- 一份中文 Markdown
- 一个 `figures/` 目录
- Markdown 中通过相对路径引用图片

结构示意：

```text
rendered/
├── An Empirical Study of Multi-Agent Collaboration for Automated Research.translation.rendered.md
└── figures/
    ├── figure-01-page-5.png
    ├── figure-02-page-10.png
    └── figure-03-page-11.png
```

## 中文翻译效果示例

下面是一小段真实风格的输出片段：

```md
# 多智能体协作在自动化研究中的实证研究

## 翻译说明

本文中文稿基于论文的 GLM-OCR 结果整理翻译，整体覆盖了标题、摘要、引言、相关工作、方法、实验结果、结论和主要图表说明。

### 摘要

随着 AI agents 的不断发展，研究社区正迅速从单一大语言模型（LLM）转向多智能体系统（Multi-Agent Systems, MAS），以突破自动化研究中的认知瓶颈。

### 图 1

![](./figures/figure-01-page-5.png)
```

## 为什么这个 Demo 有说服力

它展示的不是“模型会翻译一句话”，而是这套 skill 的完整交付能力：

- 原始 PDF 会被保留
- 翻译前先走 OCR，而不是让模型直接脑补整篇论文
- 中文全文默认保留图表
- 输出结果是长期可归档的 Markdown，而不是一次性聊天记录

## 如何复现

下面是最短复现路径：

```bash
python3.12 scripts/archive_paper.py \
  --arxiv-id 2603.29632v1 \
  --query "ai agents" \
  --archive-dir /tmp/papers/archive
```

```bash
python3.12 scripts/ocr_paper.py \
  --arxiv-id 2603.29632v1 \
  --archive-dir /tmp/papers/archive
```

```bash
python3.12 scripts/translate_paper.py \
  --arxiv-id 2603.29632v1 \
  --archive-dir /tmp/papers/archive \
  --translation-dir /tmp/papers/translations
```

```bash
python3.12 scripts/render_ocr_figures.py \
  --pdf "/tmp/papers/archive/An Empirical Study of Multi-Agent Collaboration for Automated Research/An Empirical Study of Multi-Agent Collaboration for Automated Research.pdf" \
  --ocr-md "/tmp/papers/archive/An Empirical Study of Multi-Agent Collaboration for Automated Research/An Empirical Study of Multi-Agent Collaboration for Automated Research.md" \
  --ocr-response-json "/tmp/papers/archive/An Empirical Study of Multi-Agent Collaboration for Automated Research/ocr_response.json" \
  --output-dir /tmp/papers/rendered
```

## 适合放在哪里展示

这个 demo 很适合放在：

- GitHub 首页 README
- 发布帖的第一张图或第一段说明
- Claude Code / Codex skill 介绍页
- Obsidian 知识库工作流说明
