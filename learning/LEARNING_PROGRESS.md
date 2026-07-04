# Agent Study 学习进度

> 状态日期：2026-07-03

## 1. 环境状态

| 项目 | 状态 | 证据 |
| --- | --- | --- |
| Apple Silicon 环境 | 已完成 | `arm64` Mac |
| Python | 已完成 | `.venv` 中的 Python 3.12.13 |
| 本地推理 | 已完成 | `llama-cpp-python` 可以导入并运行 |
| 模型 | 已完成 | `models/llama-3-8b-instruct.gguf`，约 4.7 GB |
| 项目检查 | 已完成 | `setup_check.py` 全部通过 |
| Git 远程管理 | 已完成 | `origin` 为个人 fork，`upstream` 为原项目 |

## 2. 课程状态

状态含义：

- **已完成练习**：手敲、运行并讨论过主要数据流；
- **学习中**：正在实现或验证本课概念；
- **待学习**：尚未系统进入本课。

| Lesson | 状态 | 学习证据与当前理解 |
| --- | --- | --- |
| 01 Basic LLM | 已完成练习 | `lesson_01_practice.py`；理解 GGUF -> Llama -> response text |
| 02 System Prompt | 已完成练习 | `lesson_02_practice.py`；理解角色 prompt 的拼接 |
| 03 Structured Output | 已完成练习 | `lesson_03_practice.py`；理解 JSON 文本 -> Python dict 和重试 |
| 04 Decisions | 已完成练习 | `lesson_04_practice.py`；理解有限选项和决策校验 |
| 05 Tools | 已完成练习 | `lesson_05_practice.py`；计算器请求和执行得到 `294` |
| 06 Loop and State | 已完成练习 | `lesson_06_practice.py`；理解 step、state、`done` 和 `max_steps` |
| 07 Memory | 已完成练习 | `lesson_07_practice.py`；理解 memory 位于模型权重之外 |
| 08 Planning | 已完成练习 | `lesson_08_practice.py`；生成并模拟执行五步计划 |
| 09 Atomic Actions | 已完成练习 | `lesson_09_practice.py`；把 plan step 转换为 action 和 inputs |
| 10 AoT Graph | 已完成练习 | `lesson_10_practice.py`；校验依赖并按顺序执行节点 |
| 11 Evals | 学习中 | 最小 Decision Eval 位于 `test.py`；已理解 golden input、expected、actual 和报告 |
| 12 Telemetry | 待学习 | 曾运行仓库演示，但尚未系统学习源码和数据流 |

## 3. Git 学习证据

| Commit | 学习内容 |
| --- | --- |
| `52dc2d9` | 直接调用 LLM |
| `ab88ace` | 把 LLM 调用封装进 Agent 类 |
| `9ca7b01` | System Prompt |
| `56a2ef8` | JSON 结构化输出 |
| `50a4b06` | 决策路由与解析改进 |
| `f45e521` | 计算器工具 |
| `7d4a9a4` | Loop、State 和 max_steps |
| `547754b` | 进程内短期记忆 |
| `5b0565b` | Plan 生成与模拟执行 |
| `dd6f11b` | Atomic Action |
| `2c41bc3` | AoT 依赖图 |

## 4. 当前优势

- 能沿列表、字典、循环和函数返回值追踪具体数据；
- 能区分模型生成的 JSON 文本与 Python 解析后的字典；
- 理解工具、记忆、计划和状态都属于模型外部工程能力；
- 能沿 `complete_example.py`、`agent/agent.py`、helper 和练习文件追踪调用链；
- 已开始通过打印中间变量定位数据流中的错误。

## 5. 正在巩固的知识

- Python import 路径、package、module、class、object 和 `self`；
- 先设计输入输出契约，再写实现；
- 区分“格式有效但答案错误”和“无法解析”；
- 区分模拟执行与真实工具执行；
- 把一次成功运行变成可重复的回归证据。

## 6. Lesson 11 当前数据流

```text
DECISION_GOLDEN 提供 input 和 expected
  -> evaluate_decisions()
  -> Agent.decide()
  -> 模型输出解析为 actual
  -> actual 与 expected 比较
  -> result 加入 results
  -> 打印 pass/fail 报告
```

当前仓库事实：

- `test.py` 保存当前最小 Decision Eval；
- `lesson_11_practice.py` 仍是 Lesson 10 AoT 练习副本；
- 在正确的 Lesson 11 文件中重写并运行 Eval 前，本课保持“学习中”。

## 7. 立即执行的下一步

1. 在 `lesson_11_practice.py` 中从零重写最小 Decision Eval；
2. 运行并把失败分类为无决策、错误决策、异常或评测器缺陷；
3. 对照 `agent/evals.py` 追踪正式源码；
4. 增加一个结构化输出、一个工具和一个记忆循环案例；
5. Lesson 11 验收后单独提交；
6. 按同样流程进入 Lesson 12。

## 8. 每次学习后的更新清单

- [ ] 更新课程状态和日期
- [ ] 记录练习文件和运行证据
- [ ] 记录新掌握的概念
- [ ] 记录遗留疑问或失败模式
- [ ] 练习完成后记录 Git commit
- [ ] 写下下一步最小行动

