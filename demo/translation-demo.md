# PDF -> 中文 Markdown Demo

这个 demo 展示一条最小翻译链路：

- 输入一篇英文论文 PDF
- 输出一份适合 VS Code / Obsidian 阅读的带图中文 Markdown

## 示例论文

- 论文标题：`Attention Is All You Need`
- 论文来源：arXiv
- 方向：Transformer / machine translation / attention

## 输入

精简后的 demo 目录里直接保留原始 PDF：

```text
demo/attention-is-all-you-need/
└── Attention Is All You Need.pdf
```

## 输出

最终交付物不是纯文本，而是：

- 一份中文 Markdown
- 一个 `figures/` 目录
- Markdown 中通过相对路径引用图片

结构示意：

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

## 中文翻译效果示例

下面是一小段真实风格的输出片段：

```md
# 注意力就是你所需要的一切

## 翻译说明

本文中文稿基于 GLM-OCR 结果整理翻译。OCR 结果保留了标题、章节结构、公式、表格和主要图片位置，因此这一版更接近论文原始排版。

### 摘要

主流的序列转导模型通常依赖复杂的循环神经网络或卷积神经网络，并采用编码器-解码器结构。表现最好的模型往往还会通过注意力机制把编码器和解码器连接起来。本文提出了一种新的、更加简洁的网络结构 Transformer，它完全建立在注意力机制之上，彻底移除了递归和卷积。

### 图 1

![](./figures/figure-01-page-3.png)
```

## Demo 内容

- 原始 PDF 会被保留
- 翻译前先走 OCR，而不是让模型直接脑补整篇论文
- 中文全文默认保留图表
- demo 目录最终可以精简成只保留 PDF、带图中文稿和 `figures/`

## 如何复现

下面是最短复现路径：

```bash
python3.12 scripts/archive_paper.py \
  --arxiv-id 1706.03762v7 \
  --query "Attention Is All You Need" \
  --archive-dir /tmp/papers/archive
```

```bash
python3.12 scripts/ocr_paper.py \
  --arxiv-id 1706.03762v7 \
  --archive-dir /tmp/papers/archive
```

```bash
python3.12 scripts/translate_paper.py \
  --arxiv-id 1706.03762v7 \
  --archive-dir /tmp/papers/archive \
  --translation-dir /tmp/papers/translations
```

```bash
python3.12 scripts/render_ocr_figures.py \
  --pdf "/tmp/papers/archive/Attention Is All You Need/Attention Is All You Need.pdf" \
  --ocr-md "/tmp/papers/archive/Attention Is All You Need/Attention Is All You Need.md" \
  --ocr-response-json "/tmp/papers/archive/Attention Is All You Need/ocr_response.json" \
  --output-dir /tmp/papers/rendered
```

## 可展示位置

- GitHub 首页 README
- 发布帖的第一张图或第一段说明
- Claude Code / Codex skill 介绍页
- Obsidian 知识库工作流说明
