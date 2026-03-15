# EnglishLearning

[English README](README.md)

EnglishLearning 是一个个人使用的英语词组制卡工作台。你可以输入一个或多个英文单词，用 Gemini 生成完整解析，从复制专用格式中提取词组对，人工筛选后再提交到 Anki。

## 快速了解

- 支持多个输入块，适合批量生成
- 页面保留完整 AI 响应，方便人工审核
- 提取出的词组对可继续编辑
- 最终提交结果使用卡片式预览
- 重复 `Front` 支持手动锁定优先保留
- 通过 AnkiConnect 选择本地 deck 并提交

## 这个项目能做什么

- 为一个或多个输入单词生成完整 AI 解析
- 从特殊复制格式中提取词组对
- 在提交前编辑、勾选、取消勾选，并锁定重复的 `Front`
- 用卡片式预览展示最终会提交到 Anki 的结果
- 通过 AnkiConnect 把选中的词组对提交到 Anki

## 使用流程

1. 在本地网页中输入一个或多个英文单词。
2. 点击生成按钮，请求 AI 输出。
3. 查看完整响应和提取出的词组对。
4. 按需修改 `Front` 和 `Back`。
5. 可取消勾选低价值词组；如果有重复 `Front`，也可以锁定你想保留的那一条。
6. 查看最终提交卡片预览。
7. 选择目标 deck，并提交到 Anki。

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
- 最终会发送到 Anki 的卡片式预览

这样既能保留 AI 原始解析，也能在提交前人工收口出更干净的学习卡片。

## 关键规则

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
- `COPY_FORMAT_PROMPT_FILE`: 覆盖本地 prompt 文件路径
- `COPY_FORMAT_GEMINI_MODEL`: 覆盖 Gemini 模型名，默认值为 `gemini-2.5-pro`

示例：

```bash
COPY_FORMAT_WEB_PORT=8042 \
COPY_FORMAT_GENERATION_CALLABLE=/absolute/path/to/local_generation_adapter.py:generate_word \
uv run python -m src.web_entrypoint
```

## 不提交到 Git 的本地文件

以下文件会被有意忽略：

- `key`
- `英语二的备考prompt.txt`

这样可以避免把个人凭据和本地 prompt 调整提交到版本控制。

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
- 如果本地 Gemini 配置不可用，应用会回退到内置的演示生成适配器。
- 如果你曾经泄露过真实 Gemini key，继续使用前请先轮换。
