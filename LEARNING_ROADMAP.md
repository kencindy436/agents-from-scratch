# Agent Study 学习大纲与技术路线

> 文档日期：2026-06-29  
> 适用项目：`AI Agents from Scratch`  
> 当前判断：第 1～6 课已有学习与实践记录，下一阶段从第 6 课复盘后进入第 7 课。

## 1. 如何理解当前进度

“写过练习”不等于“已经掌握”。本路线用以下证据判断学习进度：

- 仓库中存在 `lesson_01_practice.py`～`lesson_06_practice.py`。
- Git 提交依次记录了 LLM 调用、系统提示词、JSON 输出、决策、工具和 Agent Loop。
- 第 6 课练习已经包含 `AgentState`、循环和 `max_steps`。
- 尚未发现第 7～12 课对应的个人练习文件或学习日志。

因此，第 1～6 课标记为“有学习证据、需要复盘验收”，而不是直接标记为“完全掌握”。

### 当前能力边界

已经走完的主线是：

```text
文本生成 → 行为约束 → JSON 契约 → 有限决策 → 工具请求/执行 → 带状态的循环
```

接下来的主线是：

```text
跨交互记忆 → 计划数据 → 原子动作 → 依赖图 → 回归评测 → 运行时可观测性
```

当前正位于“最小 Agent 内核”与“可持续 Agent 系统”的分界处。

## 2. 整体技术路线与项目全景

### 2.1 总体目标

这套课程的技术路线不是不断给模型增加 Prompt，而是给一个概率模型逐层加上确定性的工程外壳：

```text
概率文本生成
  → 可解析的输出契约
  → 有限且可校验的动作空间
  → 由程序控制的真实执行
  → 显式状态、记忆和任务结构
  → 可回归测试、可追踪的运行系统
```

最终目标不是得到一个“更像人”的聊天机器人，而是得到一个行为边界清楚、失败可以定位、结果能够验证的本地 Agent。

### 2.2 三条并行演进路线

12 课可以看成三条相互配合的技术主线：

| 主线 | 演进过程 | 解决的问题 |
| --- | --- | --- |
| 输出与控制线 | 自由文本 → 系统提示词 → JSON 契约 → 有限决策 → 结构化工具调用 | 如何把不稳定的模型输出变成程序可以安全消费的指令？ |
| 状态与任务线 | 单次调用 → Agent Loop → Memory → Plan → Atomic Action → Dependency Graph | 如何让一次回答演化成可以持续推进的多步任务？ |
| 质量与观测线 | 解析校验/重试 → Golden Evals → Trace/Span/Metrics | 如何发现行为退化，并解释运行时到底发生了什么？ |

三条路线不是彼此独立的功能列表。输出契约是决策、工具、计划和评测的共同基础；显式状态让循环、记忆和计划能够衔接；评测与遥测则反过来验证前两条路线是否可靠。

### 2.3 端到端运行链路

目标形态下，一次 Agent 任务的完整数据流是：

```text
用户目标
  ↓
Agent 包装层构造 Prompt、允许动作和输出契约
  ↓
LocalLLM 调用本地 GGUF 模型生成候选输出
  ↓
utils 解析 JSON，Agent 校验字段、枚举和参数
  ↓
Python 执行白名单工具，或更新 memory / plan / state
  ↓
执行结果成为下一轮 observation
  ↓
循环继续，直到 done / error / max_steps

离线：Evals 用固定输入检查行为是否回归
在线：Telemetry 用同一 trace ID 记录每个 span 和指标
```

当前项目已经分别提供了这些部件，但还没有把它们全部接成完整闭环。例如第 6 课循环尚未执行 action 并回填新 observation，计划和 AoT 的执行函数也仍是教学占位实现。这正是后续综合项目需要完成的连接工作。

### 2.4 为什么按这个顺序学习

1. **先约束输出，再开放动作。** 如果 JSON、字段和选项还不可靠，接入真实工具只会放大错误。
2. **先建立状态和终止，再增加长期能力。** Loop 是 Memory 和 Planning 的运行骨架，`max_steps` 是最早的安全边界。
3. **先把计划变成数据，再处理复杂依赖。** 顺序列表容易观察；原子动作和依赖图是在这个基础上逐步消除歧义。
4. **最后形成质量闭环。** Evals 负责回答“改动后是否仍然有效”，Telemetry 负责回答“这次运行具体发生了什么”。

### 2.5 代码分层

项目的核心不是某个复杂 Prompt，而是一组职责明确的机械部件：

| 层次 | 主要文件 | 职责 |
| --- | --- | --- |
| 本地推理层 | `shared/llm.py` | 加载 GGUF 模型，完成 text in / text out |
| 解析与契约层 | `shared/utils.py`、`agent/agent.py` | 提取 JSON、校验字段、失败重试 |
| Agent 内核 | `agent/agent.py`、`agent/state.py` | 组织决策、步骤、状态和终止条件 |
| 能力执行层 | `agent/tools.py` | 定义工具接口，并由 Python 代码实际执行 |
| 上下文与任务层 | `agent/memory.py`、`agent/planner.py` | 记忆、计划、原子动作和依赖图 |
| 质量保障层 | `agent/evals.py`、`evals/golden_datasets.py` | 用固定案例发现行为回归 |
| 可观测层 | `agent/telemetry.py` | 记录 span、trace、延迟、成功率和重试 |

最重要的职责边界是：

- 模型负责生成候选文本、选择候选动作、填写结构化参数。
- Agent 包装层负责提供选项、解析和校验输出、控制重试、管理状态与终止。
- 普通 Python 代码负责真正执行工具、存储数据、排列依赖和记录日志。
- 模型并不直接拥有工具、记忆或执行权限；它只看到被放进 Prompt 的信息。

## 3. 四阶段学习大纲

| 阶段 | 课程 | 核心问题 | 阶段产物 | 通过标准 |
| --- | --- | --- | --- | --- |
| A. LLM 基础 | 01～03 | 如何把概率文本变成可消费的数据？ | 本地模型封装、系统提示词、JSON 契约 | 能解释 temperature、context、解析、校验与重试 |
| B. 最小 Agent | 04～06 | 如何让模型选择动作并安全地循环？ | 路由、工具调用、状态机、终止条件 | 能区分“请求动作”和“执行动作”，能定位循环不推进的原因 |
| C. 任务系统 | 07～10 | 如何处理跨轮信息和复杂任务？ | 记忆、顺序计划、原子动作、依赖图 | 能把目标转成可检查的数据，并按依赖安全执行 |
| D. 可靠性系统 | 11～12 | 如何知道 Agent 是否退化、运行时发生了什么？ | golden evals、trace、metrics | 能用评测拦截回归，用 trace 定位一次失败 |

## 4. 已学内容复盘：第 1～6 课

下面按项目规定的四个问题整理每课结论。

### Lesson 01：Basic LLM Chat

- 新增能力：加载本地模型，完成一次最小文本生成。
- 代码入口：`complete_example.py::lesson_01_basic_chat()` → `Agent.simple_generate()` → `LocalLLM.generate()`。
- 模型与包装层：模型预测后续 token；包装层配置模型路径、上下文、最大生成长度和停止词。
- 失败模式或问题：输出可能截断、重复或波动；此时还没有结构化契约，也没有 Agent 行为。

### Lesson 02：System Prompt

- 新增能力：通过系统提示词约束角色、语气、语言和回答方式。
- 代码入口：`complete_example.py::lesson_02_with_role()` → `Agent.generate_with_role()`。
- 模型与包装层：模型仍只生成 token；包装层负责拼接 system/user/assistant 格式并清理标签。
- 失败模式或问题：Prompt 只能改变输出概率，不能保证服从；过长 Prompt 还会占用上下文。

### Lesson 03：Structured Output

- 新增能力：要求模型返回 JSON，并在解析失败时重试。
- 代码入口：`complete_example.py::lesson_03_structured()` → `Agent.generate_structured()` → `extract_json_from_text()`。
- 模型与包装层：模型生成 JSON 候选；包装层设置低温度、提取 JSON、检查解析结果并控制三次重试。
- 失败模式或问题：当前校验主要确认“能解析”，还没有完整检查字段类型、枚举和嵌套结构。

### Lesson 04：Decision Making

- 新增能力：让模型从有限动作集合中选择一个路由。
- 代码入口：`complete_example.py::lesson_04_decisions()` → `Agent.decide()`。
- 模型与包装层：模型做语义分类；包装层提供允许集合，并拒绝集合之外的输出。
- 失败模式或问题：选项含义重叠时决策会不稳定；必须保留 `decision in choices` 这一信任边界。

### Lesson 05：Tools

- 新增能力：模型生成带参数的工具请求，系统再执行具体 Python 函数。
- 代码入口：`complete_example.py::lesson_05_tools()` → `Agent.request_tool()` → `Agent.execute_tool_call()` → `agent.tools.execute_tool()`。
- 模型与包装层：模型选择工具和参数；包装层校验工具请求并控制执行；计算结果来自 `calculator()`，不是模型心算。
- 失败模式或问题：个人练习中的操作名写成了 `substract`，但 Prompt 使用 `subtract`，减法请求会在执行阶段失败；当前请求校验也没有完整覆盖工具白名单、参数类型和必填字段。

### Lesson 06：Agent Loop

- 新增能力：在显式状态和终止条件控制下重复执行 agent step。
- 代码入口：`complete_example.py::lesson_06_agent_loop()` → `Agent.run_loop()` → `Agent.agent_step()` → `AgentState`。
- 模型与包装层：模型为每步建议 `action` 和 `reason`；包装层递增步骤、收集结果、识别 `done` 并用 `max_steps` 防止无限循环。
- 失败模式或问题：实际运行连续三次选择 `analyze`，最后由 `max_steps=3` 停止。原因是循环只改变步骤计数，没有执行动作，也没有把动作结果作为新观察反馈给下一轮。个人练习还把终止字段写成了 `actions`，而模型契约字段是 `action`；官方 `agent/agent.py` 与 `test.py` 使用的是正确字段。

### 第 1～6 课的综合心智模型

```text
用户输入
  ↓
Prompt 给模型有限的输出空间
  ↓
模型生成候选 JSON
  ↓
Python 解析、校验、拒绝或重试
  ↓
Python 执行允许的动作并更新显式状态
  ↓
新观察进入下一轮，直到 done / error / max_steps
```

Agent 的可靠性主要来自循环外的工程约束，而不是来自模型“更聪明”。

## 5. 进入第 7 课前的复盘关卡

建议先完成下面三个小实验，再继续增加能力：

1. 统一第 5 课中的 `subtract` 拼写，并分别验证加、减、乘、除和除零。
2. 用一个固定返回 `{"action": "done"}` 的假模型验证第 6 课能否提前终止，比较个人练习与正式实现。
3. 给循环增加一个最小的“执行结果/新观察”，观察模型是否仍然重复 `analyze`。

通过标准：能够用自己的话解释为什么“有 while 循环”还不等于“任务会推进”。

## 6. 后续技术路线：第 7～12 课

### Lesson 07：Memory

- 先读：`lessons/07_memory.md`。
- 示例入口：`complete_example.py::lesson_07_memory()`。
- 实现链路：`Agent.run_with_memory()` → `Memory.add()/get_all()`。
- 预测题：第二次调用为什么能回答 Alice？模型本身是否真的保存了 Alice？
- 最小实验：存入姓名，再查询姓名，同时打印 `agent.memory.get_all()`。
- 验收：能区分 prompt context、进程内 memory 和磁盘持久化；知道当前 `Memory` 只在 Agent 实例生命周期内有效。

### Lesson 08：Planning

- 先读：`lessons/08_planning.md`。
- 示例入口：`complete_example.py::lesson_08_planning()`。
- 实现链路：`Agent.create_plan()` → `planner.create_plan()` → `Agent.execute_plan()`。
- 预测题：计划生成成功后，`execute_plan()` 是否真的完成了计划内容？
- 最小实验：为一个具体目标生成计划，手动删除或调整一个步骤后再执行。
- 验收：能解释“计划是 JSON 数据，不是隐藏思维”；能指出当前执行器只是把步骤标记为已执行。

### Lesson 09：Atomic Actions

- 先读：`lessons/09_atomic_actions.md`。
- 示例入口：`complete_example.py::lesson_09_atomic_actions()`。
- 实现链路：`Agent.create_atomic_action()` → `planner.create_atomic_action()`。
- 预测题：把“写文章”转换成一个 action 后，它是否已经足够小、足够可验证？
- 最小实验：把同一模糊步骤转换多次，比较 action 名和 inputs 的稳定性。
- 验收：每个动作都能单独校验、执行和报告失败；不接受只有 action、缺少有效 inputs 的结果。

### Lesson 10：Atom of Thought / Dependency Graph

- 先读：`lessons/10_atom_of_thought.md`。
- 示例入口：`complete_example.py::lesson_10_aot()`。
- 实现链路：`Agent.create_aot_plan()` → `planner.create_aot_graph()` → `execute_graph()`。
- 预测题：两个无依赖节点能否并行？循环依赖会产生什么结果？
- 最小实验：手写一个菱形依赖图，记录实际执行顺序；再构造缺失依赖和环。
- 验收：能解释拓扑执行、依赖满足和 DAG；能发现当前实现尚未真正并行，也没有完整拒绝重复 ID、缺失依赖和环。

### Lesson 11：Evals

- 先读：`lessons/11_evals.md`。
- 示例入口：`complete_example.py::lesson_11_evals()`。
- 实现链路：`AgentEval` → `evals/golden_datasets.py` → 各 Agent 能力入口。
- 预测题：Prompt 改得更自然后，哪些 JSON 或工具行为可能悄悄退化？
- 最小实验：只运行每个 suite 的首个案例，不直接运行全部课程示例。
- 验收：能区分硬断言和软断言；为第 6 课增加“done 提前终止”和“max_steps 兜底”案例。

### Lesson 12：Telemetry

- 先读：`lessons/12_telemetry.md`。
- 示例入口：`complete_example.py::lesson_12_telemetry()`。
- 实现链路：`Telemetry.start_trace()` → `log_*()` → JSONL spans / metrics。
- 预测题：eval 全通过时，为什么仍然需要 trace 和延迟指标？
- 最小实验：只跟踪一次结构化输出和一次工具调用，并按 trace ID 还原顺序。
- 验收：一次完整 Agent 交互共享同一 trace ID；可以看到调用时长、成功/失败和重试次数；运行日志不提交到 Git。

## 7. 推荐学习节奏

每次只推进一个概念，保持固定流程：

1. 先写下对输出、状态变化和失败位置的预测。
2. 阅读对应 `lessons/XX_*.md`。
3. 找到 `complete_example.py` 中同名示例函数。
4. 追踪到 `agent/agent.py` 的公开入口。
5. 只在需要时继续读 helper 文件。
6. 运行当前课程的最小示例，不运行全部 12 课。
7. 比较预测与输出，记录不一致的原因。
8. 用中文写下本课的四条结论。

建议按七个学习会话推进：

| 会话 | 内容 | 主要产物 |
| --- | --- | --- |
| 0 | 第 5～6 课复盘 | 修正工具契约认知，解释 loop 为什么不推进 |
| 1 | 第 7 课 | 一次可检查的记忆存取循环 |
| 2 | 第 8 课 | 可人工修改的计划 JSON |
| 3 | 第 9 课 | 带参数校验的原子动作 |
| 4 | 第 10 课 | 可验证的依赖图和执行顺序 |
| 5 | 第 11 课 | 覆盖核心能力的最小 golden dataset |
| 6 | 第 12 课与综合项目 | 一次可评测、可追踪的完整 Agent 运行 |

## 8. 综合项目路线

完成 12 课后，不要立刻引入 Agent 框架。先用现有代码完成一个小型综合项目：

**目标：构建一个可观测的本地任务 Agent。**

建议最小闭环：

```text
用户目标
  → 有限路由
  → 生成并校验计划
  → 转换为原子动作/依赖图
  → 调用白名单工具
  → 把执行结果作为新观察
  → 更新状态并终止
  → eval 验证关键行为
  → telemetry 记录整条 trace
```

最终验收标准：

- 每个模型输出都有结构化契约、校验和失败路径。
- 每个真实动作都经过工具白名单，不由模型直接执行。
- 循环能因 `done`、错误或 `max_steps` 明确终止。
- 计划与执行结果是可检查的数据，不隐藏在文本中。
- 至少覆盖结构化输出、路由、工具、记忆和终止条件的 golden cases。
- 一次运行可以通过 trace ID 还原 LLM 调用、工具调用和状态变化。

## 9. 带着问题阅读当前实现

这些不是要求立即重构的任务，而是后续课程很好的观察点：

- `agent/agent.py` 内仍然硬编码了多段 Prompt，而 `shared/prompts.py` 中的模板当前几乎没有被调用。
- `get_tool_schema()` 已定义并导入，但 `Agent.request_tool()` 仍然硬编码 calculator 描述。
- `Memory` 是进程内列表，不是跨进程持久化存储。
- `execute_plan()` 和 `execute_aot_plan()` 目前是教学占位实现，没有连接真实工具。
- `create_aot_graph()` 的实际校验弱于课程文字描述，需要补充唯一 ID、依赖存在性和环检测。
- `AgentEval.test_tool_calls()` 的参数不匹配分支仍会继续给同一案例添加通过结果，学习第 11 课时应先为评测器本身写测试。
- Telemetry 由示例代码手动包裹调用，尚未成为 Agent 内核的统一横切能力。
- `setup_check.py` 能确认依赖和模型文件存在，但不能保证 Metal/CPU 后端真的能创建推理 context。

这些差距恰好构成从“教学示例”走向“可靠系统”的技术路线，不必在学习前一次性修完。

## 10. 每课学习记录模板

```markdown
## Lesson XX：主题

- 我的预测：
- 实际输出：
- 差异与原因：

### 四条结论

1. 新增了什么能力？
2. 哪个代码入口实现它？
3. 哪些工作属于模型，哪些属于 Agent 包装层？
4. 观察到了什么失败模式或仍有什么问题？

### 掌握验证

- [ ] 不看代码能画出调用链
- [ ] 能修改一个输入并预测输出变化
- [ ] 能解释一个失败案例
- [ ] 能写一个最小验证案例
```

## 11. 当前最优下一步

先做第 6 课的闭环复盘，而不是直接跳到 Memory：让 `action` 触发一个真实但安全的执行结果，并把结果作为下一轮 observation。理解“循环如何获得新信息并推进”后，再进入第 7 课，记忆系统会自然得多。
