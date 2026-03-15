# EnglishLearning

[English README](README.md)

一个把 Gemini 生成的英语词组解析人工筛选后再提交到 Anki 的本地工作台。

EnglishLearning 是一个本地制卡工作台，用来生成、审核、编辑并提交真正有价值的词组卡片，同时保留完整 AI 上下文方便人工判断。

## GitHub 仓库速览

- 这是个人工具，不是公共 SaaS 产品
- 仓库内自带的 prompt 文件是必需文件，不是可选示例
- 可以对一个或多个输入词调用 Gemini 生成词组解析
- 页面保留完整 AI 输出，方便人工筛选真正值得入卡的内容
- 支持编辑提取出的 `Front` / `Back`，处理重复 `Front`，只提交你确认过的卡片
- 支持保存审核会话并在之后恢复，整个流程以本地使用为主

仓库短描述建议：

```text
Personal English phrase card workspace with Gemini generation, manual review, and Anki submission.
```

## 文档导航

- 英文文档入口：[`docs/README.md`](docs/README.md)
- 中文文档入口：[`docs/README.zh-CN.md`](docs/README.zh-CN.md)
- 英文场景索引：[`docs/scenario/README.md`](docs/scenario/README.md)
- 中文场景索引：[`docs/scenario/README.zh-CN.md`](docs/scenario/README.zh-CN.md)
- 英文贡献说明：[`CONTRIBUTING.md`](CONTRIBUTING.md)
- 中文贡献说明：[`CONTRIBUTING.zh-CN.md`](CONTRIBUTING.zh-CN.md)

## 快速了解

- 支持多个输入块，适合批量生成
- 大批量审核时有置顶概览条，方便持续查看进度
- 页面保留完整 AI 响应，方便人工审核
- 提取出的词组对可继续编辑
- 最终提交结果使用卡片式预览
- 重复 `Front` 支持手动锁定优先保留
- 支持保存和恢复审核会话，不必重新生成
- 提交后会更清楚地区分已加入、已跳过和失败项
- 通过 AnkiConnect 选择本地 deck 并提交

## 页面截图

![审核工作台截图](docs/images/review-workspace.png)

## 这个项目能做什么

- 为一个或多个输入单词生成完整 AI 解析
- 从特殊复制格式中提取词组对
- 在提交前编辑、勾选、取消勾选，并锁定重复的 `Front`
- 在批量审核时持续显示审核概览
- 用卡片式预览展示最终会提交到 Anki 的结果
- 可以把当前审核状态导出为会话内容，稍后再恢复
- 提交后会按已加入、已跳过、提交失败分组展示反馈
- 通过 AnkiConnect 把选中的词组对提交到 Anki

## 使用流程

1. 在本地网页中输入一个或多个英文单词。
2. 点击生成按钮，请求 AI 输出。
3. 查看完整响应和提取出的词组对。
4. 按需修改 `Front` 和 `Back`。
5. 可取消勾选低价值词组；如果有重复 `Front`，也可以锁定你想保留的那一条。
6. 如果想中途暂停，可以先保存当前审核会话。
7. 查看最终提交卡片预览。
8. 选择目标 deck，并提交到 Anki。
9. 查看按结果分组的提交反馈。

## 使用示例

输入词：

```text
take
bring
```

页面会让你审核这些内容：

- 每个输入词对应的完整 Gemini 响应
- 从复制专用格式中提取出的词组对
- 每条是否提交的勾选框
- 当出现重复 `Front` 时用于指定保留项的锁定控件
- 批量审核时始终可见的概览区
- 最终会发送到 Anki 的卡片式预览
- 用于保存和恢复当前审核状态的会话区
- 按已加入、已跳过、失败分类的提交反馈

这样既能保留 AI 原始解析，也能在提交前人工收口出更干净的学习卡片。

## 界面重点

虽然这次还没有附上仓库内截图，但当前审核页的结构已经比较清晰，核心区域包括：

- 一个或多个输入词块
- 适合批量审核的置顶概览区
- 每个词对应的完整 Gemini 响应
- 可编辑的 `Front` / `Back` 词组对
- 用于勾选和锁定重复项的控制区
- 提交到 Anki 之前的卡片式预览区
- 用于暂停和恢复审核工作的会话保存区
- 提交后更清晰的结果反馈卡片

这样既保留了 AI 原始上下文，也让最终提交集合更容易人工确认。

## Roadmap

- GitHub 规划 issue: [#1 Track next workflow improvements](https://github.com/Amo-zwk/EnglishLearning/issues/1)
- 已完成: [#2 Improve review layout for larger batches](https://github.com/Amo-zwk/EnglishLearning/issues/2)
- 已完成: [#3 Support saving and restoring review sessions](https://github.com/Amo-zwk/EnglishLearning/issues/3)
- 已完成: [#4 Add clearer Anki submission feedback](https://github.com/Amo-zwk/EnglishLearning/issues/4)
- README 已补充当前页面截图；后续如果合适，也可以继续增加 GIF 展示。
- 后续迭代仍然以实用的小步优化为主，不把它扩展成公共 SaaS 产品。

## 关键规则

- 仓库中的 `英语二的备考prompt.txt` 是项目必需文件。
- 这套工作流和该 prompt 绑定，不能随意更换其他 prompt 后还期待得到同样的提取契约。
- 只有从复制专用格式中提取出的内容才会用于 Anki 提交。
- 没有价值的词组不要添加。
- Note Type 固定使用内置 `Basic`。
- `Front` 是英文词组。
- `Back` 是中文释义。
- 查重基于 `Front`。
- 如果存在重复 `Front`，优先保留被锁定的项；如果都没锁定，则保留第一个已勾选项。

## 技术栈

- Python 3.12+
- 使用 `uv` 管理环境和执行命令
- 标准库 WSGI 服务器提供本地网页
- Gemini REST 接口用于生成解析
- AnkiConnect 用于获取 deck 列表和提交 note

## 项目结构

- `src/web_entrypoint.py`: 本地网页入口与前端脚本
- `src/review_workspace.py`: 审核状态、导出逻辑、预览逻辑、提交流程
- `src/gemini_generation_adapter.py`: Gemini 适配器与本地配置加载
- `src/anki_submission_gateway.py`: AnkiConnect 集成与重复处理
- `src/ai_generation_orchestrator.py`: 多输入编排与耗时统计
- `tests/`: 这套流程的单元测试和集成风格测试

## 本地运行

1. 安装依赖：

```bash
uv sync
```

2. 启动本地站点：

```bash
uv run python -m src.web_entrypoint
```

3. 打开页面：

```text
http://127.0.0.1:8031
```

## 可选配置

- `COPY_FORMAT_WEB_PORT`: 覆盖本地 HTTP 端口
- `COPY_FORMAT_GENERATION_CALLABLE`: 指向自定义本地生成适配器，格式为 `<file-path>:<callable-name>`
- `GEMINI_API_KEY`: 从环境变量读取 Gemini key，而不是本地文件
- `COPY_FORMAT_GEMINI_KEY_FILE`: 覆盖本地 key 文件路径
- `COPY_FORMAT_PROMPT_FILE`: 仅用于把同一份必需 prompt 放到其他路径时覆盖默认位置
- `COPY_FORMAT_GEMINI_MODEL`: 覆盖 Gemini 模型名，默认值为 `gemini-2.5-pro`

示例：

```bash
COPY_FORMAT_WEB_PORT=8042 \
COPY_FORMAT_GENERATION_CALLABLE=/absolute/path/to/local_generation_adapter.py:generate_word \
uv run python -m src.web_entrypoint
```

## 项目必需文件

以下文件属于项目正式组成部分：

- `英语二的备考prompt.txt`

之所以纳入版本控制，是因为生成输出契约依赖它。

## 不提交到 Git 的本地文件

以下文件会被有意忽略：

- `key`

这样可以避免把个人凭据提交到版本控制，同时保留项目必需 prompt。

## 验证命令

运行测试：

```bash
uv run python -m unittest discover -s tests
```

检查关键模块能否编译：

```bash
uv run python -m py_compile "src/web_entrypoint.py" "src/review_workspace.py"
```

## 说明

- 这个仓库面向个人工作流，不是公共 SaaS 产品。
- 仓库自带的 prompt 文件属于产品行为的一部分，不是可替换示例。
- 如果本地 Gemini 配置不可用，应用会回退到内置的演示生成适配器。
- 如果你曾经泄露过真实 Gemini key，继续使用前请先轮换。
