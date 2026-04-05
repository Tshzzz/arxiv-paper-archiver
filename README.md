# ArXiv Paper Archiver

把 arXiv 论文一键整理成适合中文阅读、知识归档和 AI 工作流消费的研究资料。

这个 skill 面向：

- 想持续跟踪 AI / LLM / Agents / 多模态论文的人
- 想把英文论文沉淀成中文知识库的人
- 使用 Claude Code / Codex 做研究辅助的人
- 想把论文结果同步到 VS Code / Obsidian 的人

它不是一个普通的“论文搜索脚本”，而是一条完整工作流：

- 搜索论文
- 发现某个方向的热门论文
- 下载原始 PDF
- 调用 `GLM-OCR` 做版面解析
- 生成中文摘要
- 生成带图的中文全文翻译
- 输出可归档、可阅读、可二次加工的 Markdown 文件

## 一眼看懂的翻译 Demo

如果你只想判断这件事值不值得装，先看这个最小示例：

- 输入：一篇英文 PDF
- 输出：一份带图的中文 Markdown

示例论文：

- `An Empirical Study of Multi-Agent Collaboration for Automated Research`

输入文件：

```text
archive/
└── An Empirical Study of Multi-Agent Collaboration for Automated Research/
    └── An Empirical Study of Multi-Agent Collaboration for Automated Research.pdf
```

输出文件：

```text
rendered/
├── An Empirical Study of Multi-Agent Collaboration for Automated Research.translation.rendered.md
└── figures/
    ├── figure-01-page-5.png
    ├── figure-02-page-10.png
    └── figure-03-page-11.png
```

翻译成品片段：

```md
### 摘要

随着 AI agents 的不断发展，研究社区正迅速从单一大语言模型（LLM）转向多智能体系统（Multi-Agent Systems, MAS），以突破自动化研究中的认知瓶颈。然而，这些自治智能体究竟应当采用何种最优的多智能体协作框架，目前仍缺乏系统研究。

### 图 1

![](./figures/figure-01-page-5.png)
```

完整展示说明见：

- [demo/translation-demo.md](./demo/translation-demo.md)

## Demo

输入一句话：

```text
找最近一周最热门的 AI agents 论文，下载 PDF，翻译成中文并保留图表。
```

你最终可以得到：

```text
archive/
└── An Empirical Study of Multi-Agent Collaboration for Automated Research/
    ├── An Empirical Study of Multi-Agent Collaboration for Automated Research.pdf
    ├── An Empirical Study of Multi-Agent Collaboration for Automated Research.md
    ├── metadata.json
    └── ocr_response.json

summaries/
└── An Empirical Study of Multi-Agent Collaboration for Automated Research.md

translations/
└── An Empirical Study of Multi-Agent Collaboration for Automated Research.md

rendered/
├── An Empirical Study of Multi-Agent Collaboration for Automated Research.translation.rendered.md
└── figures/
```

也就是说，它会把“论文链接”变成：

- 原始 PDF
- OCR 结构化文本
- 中文摘要
- 带图中文全文
- 可直接放进知识库的 Markdown 产物

## 为什么这个 skill 更好用

### 1. 不只是搜索，而是完整论文工作流

很多工具只能帮你“找到论文”。

这个 skill 解决的是从“找到论文”到“真正可读、可存、可复用”的整条链路。

### 2. 默认按英文论文标题命名

不是把文件堆成：

- `2508.16598.pdf`
- `2508.16598.md`

而是统一按论文英文标题保存，更适合人类阅读和长期归档。

### 3. 翻译前强制走 OCR

这套 skill 明确要求：

- 全文翻译前必须先调用 `GLM-OCR`
- 不能跳过 OCR 直接让模型“凭自己理解翻”

这样能明显改善：

- 章节结构
- 图表说明
- 多栏论文排版
- 表格与公式上下文

### 4. 中文翻译默认带图

只要 OCR 能识别到 figure placeholder 或图片区：

- 中文全文翻译默认就要保留图表
- 不是只输出纯文字 Markdown

这点非常适合：

- VS Code 阅读
- Obsidian 知识库
- 团队内部研究归档

### 5. 同时适配 Claude Code / Codex

它既可以作为：

- Codex skill

也可以作为：

- Claude Code 的脚本工具包 + 工作流规范

不需要你维护两套逻辑。

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

## 适合谁用

如果你符合下面任意一种场景，这个 skill 就很适合你：

- 你想持续追踪某个 AI 子方向的论文
- 你想把英文论文沉淀成中文知识库
- 你想让 Claude Code / Codex 帮你自动整理论文
- 你想把论文导入 Obsidian 或 VS Code 做长期阅读

## 相关文档

- [SKILL.md](./arxiv-paper-archiver/SKILL.md)
- [references/claude_adapter.md](./arxiv-paper-archiver/references/claude_adapter.md)
- [references/output_format.md](./arxiv-paper-archiver/references/output_format.md)
- [references/error_policy.md](./arxiv-paper-archiver/references/error_policy.md)
