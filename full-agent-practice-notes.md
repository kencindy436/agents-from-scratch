# Full Agent Practice 学习笔记

## 当前状态

- 日期：2026-07-09
- 手敲练习代码：`/Users/cuiyuqi/agent/full_agent_practice.py`
- 参考代码：`/Users/cuiyuqi/agent/test.py`
- 当前阶段：Stage 3 参考代码已完成；手敲文件由学习者继续跟进
- 验证结果：`test.py` 已通过 Python 语法编译检查；纯 Python 工具层验证通过；完整模型推理运行由学习者手动执行

## 整合目标

前 12 节 practice 是按课程主题分别编写的独立版本。最终练习不直接堆叠这些文件，而是把能力合并到一个清晰的 `SimpleAgent` 中，完整走通：

```text
用户目标
→ 本地模型调用
→ 角色提示词
→ 结构化输出与验证
→ 决策与工具调用
→ Agent Loop、State、Memory
→ Plan、Atomic Action、AoT
→ Telemetry 记录
→ Eval 验证
```

## 为什么不能直接复制 12 个文件

- 多个文件重复定义了 `LocalLLM` 和 `SimpleAgent`。
- 同一个文件中的后一个同名类会覆盖前一个定义。
- Lesson 07–10 的 practice 主要突出当节能力，并非完整累计版本。
- Lesson 11 使用正式项目的 `Agent`，Lesson 12 当前实现的是自写 Telemetry。
- 正确方式是保留一份组件定义，再把各课的方法和数据流逐步合并。

## 文件分工

- `test.py`：参考版本，由 Codex 写入，用于展示当前阶段完整写法和对照调试。
- `full_agent_practice.py`：正式手敲练习文件，由学习者自己逐步输入和理解。
- 学习时先读 `test.py` 的稳定版本，再把理解后的代码手敲到 `full_agent_practice.py`。
- 后续不要直接覆盖 `full_agent_practice.py`，除非学习者明确要求。

## Stage 1 架构

当前代码由两层组成：

```text
SimpleAgent
└── LocalLLM
    └── llama_cpp.Llama
        └── models/llama-3-8b-instruct.gguf
```

职责划分：

- `Llama`：`llama_cpp` 提供的类，负责加载和运行 GGUF 模型。
- `LocalLLM`：我们编写的模型封装，统一生成参数和响应取值。
- `SimpleAgent`：面向用户的 Agent 封装，后续逐渐增加角色、工具、记忆和规划能力。
- GGUF：实际保存模型结构、权重和量化数据的文件。

## 当前执行链路

```text
python full_agent_practice.py
→ __name__ 等于 "__main__"
→ 创建 SimpleAgent
→ SimpleAgent.__init__ 创建 LocalLLM
→ LocalLLM.__init__ 创建 Llama 对象并加载 GGUF
→ agent.simple_generate(user_input)
→ LocalLLM.generate(prompt)
→ kwargs 保存本次生成参数
→ self.llm(**kwargs) 执行推理
→ response["choices"][0]["text"] 取得回答
→ strip() 清理首尾空白
→ assert 检查结果类型和内容
→ print 输出回答
```

## Stage 2 新增内容

Stage 2 对应 Lesson 02-04，目标是在普通文本调用基础上加入三个能力：

```text
Lesson 02：generate_with_role()
→ 把 system_prompt 和 user_input 拼成完整 prompt

Lesson 03：generate_structured()
→ 要求模型输出 JSON
→ Python 提取并解析 JSON
→ 失败时最多重试 3 次

Lesson 04：decide()
→ Python 提供 choices
→ LLM 从 choices 中选择一个 decision
→ Python 校验 decision 是否在 choices 里
```

新增辅助函数：

```python
def extract_json_from_text(text):
    start = text.find("{")

    if start == -1:
        return None

    decoder = json.JSONDecoder()

    try:
        parsed, _ = decoder.raw_decode(text[start:])
        return parsed
    except json.JSONDecodeError:
        return None
```

这个函数解决的问题是：模型输出经常不是纯 JSON，可能包含前后多余文本。代码先找到第一个 `{`，再用 `raw_decode()` 从这个位置解析出第一个完整 JSON，并转换成 Python 数据。

新增 `SimpleAgent` 方法：

- `generate_with_role(user_input)`：使用 `system_prompt` 约束模型角色。
- `generate_structured(user_input, schema)`：让模型按 schema 输出 JSON，并返回 Python `dict` 或 `None`。
- `decide(user_input, choices)`：让模型从有限选项中选择动作，返回一个字符串 decision 或 `None`。

Stage 2 的核心数据流：

```text
Python 数据
choices / schema / system_prompt / user_input
↓
整理成 prompt 字符串
↓
发给 LLM
↓
LLM 输出字符串
↓
Python 提取 JSON
↓
Python 校验 dict / key / value
↓
返回可被程序继续使用的数据
```

## Stage 3 新增内容

Stage 3 对应 Lesson 05：Tools。目标是让 Agent 不只生成文本，还能请求 Python 工具执行具体动作。

新增整体结构：

```text
用户问题
→ request_tool()
→ LLM 输出工具调用 JSON
→ extract_json_from_text()
→ Python 得到 tool_call dict
→ execute_tool_call()
→ execute_tool()
→ calculator()
→ 返回真实计算结果
```

新增工具函数：

- `calculator(a, b, operation="add")`：真正执行加、减、乘、除。
- `execute_tool(tool_name, arguments)`：根据工具名找到对应 Python 函数，并把参数字典拆成函数参数执行。

新增 Agent 方法：

- `request_tool(user_input)`：让模型根据用户输入生成工具调用请求。
- `execute_tool_call(tool_call)`：把模型请求的工具调用交给 Python 执行。

模型应该输出类似：

```json
{"tool": "calculator", "arguments": {"a": 42, "b": 7, "operation": "multiply"}}
```

Stage 3 最重要的边界：

```text
LLM 负责：选择工具名、生成参数 JSON
Python 负责：校验工具名、执行真实函数、返回真实结果
```

也就是说，模型不是在自己计算 `42 * 7`，而是在请求：

```text
请调用 calculator，参数是 a=42, b=7, operation=multiply
```

真正得到 `294` 的地方是 Python 的 `calculator()`。

## Stage 3 验证方式

当前 `test.py` 中有两层验证。

第一层：固定工具调用，不经过模型。

```python
fixed_tool_call = {
    "tool": "calculator",
    "arguments": {
        "a": 42,
        "b": 7,
        "operation": "multiply",
    },
}

fixed_tool_result = agent.execute_tool_call(fixed_tool_call)
assert fixed_tool_result == 294
```

这一步验证 Python 工具层是否正常。

第二层：让模型请求工具。

```python
tool_call = agent.request_tool("What is 42 * 7?")
tool_result = agent.execute_tool_call(tool_call)
assert tool_result == 294
```

这一步验证模型是否能按要求输出工具调用 JSON，以及 Python 是否能执行它。

调试时优先看第一层：

```text
固定工具调用失败 → Python 工具层有问题
固定工具调用成功，但 request_tool 失败 → prompt、模型输出或 JSON 解析有问题
```

## 初始化与生成

模型初始化参数主要决定模型如何加载：

```text
model_path   加载哪个 GGUF 模型
n_ctx        本次模型运行使用的上下文窗口大小
verbose      是否显示详细的底层日志
```

每次生成参数主要决定当前请求如何执行：

```text
prompt       本次输入文本
max_tokens   本次最多新生成多少 token
stop         本次遇到哪些文本时停止生成
temperature  本次生成的随机程度
```

`self.llm = Llama(...)` 创建并保存模型运行对象；`self.llm(**kwargs)` 调用这个对象执行一次生成。对象创建后，调用其能力时仍然可以继续传入本次操作所需的参数。

## 关键语法

### `max_tokens`

`max_tokens=512` 表示一次调用最多新生成 512 个 token，不限制输入 token。模型遇到结束标记或 `stop` 时可以提前结束。

### `verbose`

`verbose` 意为“详细的”。`verbose=False` 用于减少 `llama.cpp` 的底层加载和推理日志。

### `stop=None`

`None` 表示调用者没有提供自定义停止序列，代码会改用默认值：

```python
["</s>", "\n\n", "User:", "Assistant:"]
```

条件表达式：

```python
stop if stop is not None else default_stop
```

表示有自定义 `stop` 就使用它，否则使用默认停止列表。

### `**kwargs`

`kwargs` 是关键字参数字典：

```python
{
    "prompt": prompt,
    "max_tokens": self.max_tokens,
    "stop": stop_value,
}
```

`self.llm(**kwargs)` 会把字典拆成：

```python
self.llm(
    prompt=prompt,
    max_tokens=self.max_tokens,
    stop=stop_value,
)
```

### 模型响应

`llama_cpp` Completion API 返回字典。当前只取第一个候选回答的文本：

```python
response["choices"][0]["text"].strip()
```

- `choices`：候选回答列表。
- `[0]`：第一个候选回答。
- `text`：API 规定的文本字段。
- `strip()`：删除字符串首尾空格和换行。

### `system_prompt` 与 `user_input`

- `system_prompt`：规定 Agent 的长期角色、行为和约束。
- `user_input`：用户本次提出的具体请求。
- 当前 `simple_generate()` 对应 Lesson 01，只传递 `user_input`。
- 下一阶段的 `generate_with_role()` 会把两者拼成完整 Prompt。

### `find()` 与 `-1`

```python
start = text.find("{")
```

`find()` 返回查找结果的位置。如果找到了，返回 `0` 或更大的数字；如果没有找到，返回 `-1`。

```python
if start == -1:
    return None
```

这表示：如果文本里没有 `{`，就认为没有可解析的 JSON，直接返回 `None`。

### 返回值

返回值是函数运行结束后交回来的结果。比如：

```python
start = text.find("{")
```

这里 `text.find("{")` 的返回值会被保存到 `start` 中。

如果函数没有写 `return`，Python 默认返回 `None`。显式写 `return None` 通常用于表达“没有有效结果”。

### `None`

`None` 表示没有有效值，不等于“没有出错”。在当前代码中它常表示：

```text
没有找到 JSON
没有解析出有效 dict
模型没有给出可用 decision
```

### `JSONDecoder().raw_decode()`

```python
decoder = json.JSONDecoder()
parsed, _ = decoder.raw_decode(text[start:])
```

`raw_decode()` 是 Python 标准库 `json` 中 `JSONDecoder` 对象的方法。它会从字符串开头解析出一个完整 JSON，并返回两个值：

```text
parsed：解析后的 Python 数据，比如 dict
end：JSON 结束的位置
```

当前代码不使用第二个值，所以用 `_` 接住。`_` 是约定俗成的变量名，表示“这个值存在，但我不打算使用”。

### `for _ in range(3)`

```python
for _ in range(3):
```

表示最多重复执行 3 次，但不关心当前是第几次。这里用于重试模型调用，因为模型不一定第一次就输出合法 JSON。

### `join()`

```python
options = "\n".join(
    f"- {choice}"
    for choice in choices
)
```

`join()` 是字符串方法，用于把一组字符串拼接成一个字符串。这里用换行符 `\n` 连接，最终把 Python list：

```python
["answer_question", "summarize_text", "translate"]
```

转换成 prompt 中更清晰的多行文本：

```text
- answer_question
- summarize_text
- translate
```

### `schema`

`schema` 是写给模型看的输出格式合同。它不需要描述世界上所有可能数据，只描述当前这一步下一段 Python 代码需要什么结构。

示例：

```python
schema = """
{
  "topic": "string",
  "difficulty": "beginner | intermediate | advanced"
}
"""
```

含义是要求模型输出一个 JSON 对象，至少包含 `topic` 和 `difficulty` 两个字段。

schema 的边界通常和一个明确步骤对应：

```text
一个决策点
一个工具调用
一个状态更新
一个记忆保存
一个最终回答
```

不要写万能 schema；每一步只写刚好够下一步使用的小 schema。

### 封闭选择与开放生成

`choices` 不是模型生成的，而是 Python 提前提供给模型的可选范围。适用于路由、工具选择、动作选择等封闭任务。

```python
choices = [
    "answer_question",
    "summarize_text",
    "translate",
]
```

模型生成的是：

```json
{"decision": "translate"}
```

Python 再检查：

```python
parsed["decision"] in choices
```

因此原则是：

```text
需要程序执行的部分：尽量封闭
需要语言表达的部分：保持开放
```

### 工具调用

工具调用不是让模型直接执行能力，而是让模型输出一个结构化请求。

```json
{
  "tool": "calculator",
  "arguments": {
    "a": 42,
    "b": 7,
    "operation": "multiply"
  }
}
```

这个 JSON 进入 Python 后会变成 dict：

```python
{
    "tool": "calculator",
    "arguments": {
        "a": 42,
        "b": 7,
        "operation": "multiply",
    },
}
```

Python 再用：

```python
execute_tool(tool_call["tool"], tool_call["arguments"])
```

真正执行对应工具。

### `tools` 字典

```python
tools = {
    "calculator": calculator,
}
```

这里的 value 可以是函数本身。`tools["calculator"]` 取出来的就是 `calculator` 函数对象。

所以：

```python
tools[tool_name](**arguments)
```

可以理解成：

```python
calculator(a=42, b=7, operation="multiply")
```

### `lambda`

```python
"multiply": lambda x, y: x * y
```

`lambda` 是匿名小函数，适合写很短的运算逻辑。上面这一行等价于：

```python
def multiply(x, y):
    return x * y
```

### `**arguments`

如果：

```python
arguments = {
    "a": 42,
    "b": 7,
    "operation": "multiply",
}
```

那么：

```python
calculator(**arguments)
```

等价于：

```python
calculator(a=42, b=7, operation="multiply")
```

### 工具边界

工具名必须封闭，因为 Python 只能执行已经注册过的函数。

```python
if tool_name not in tools:
    raise ValueError(f"Unknown tool: {tool_name}")
```

这一步是安全边界：模型不能随便发明一个工具名并让 Python 执行。

### 程序入口

```python
if __name__ == "__main__":
```

- 直接运行文件时，`__name__` 为 `"__main__"`，执行模型测试代码。
- 被其他文件导入时，不自动加载模型和执行测试。

### 最小断言

```python
assert isinstance(result, str)
assert result
```

分别验证结果是字符串，并且不是空字符串。条件失败时会抛出 `AssertionError`。

## 本阶段提出并解决的问题

1. `Llama` 是模型吗？
   - 不是。它是 `llama_cpp` 中负责加载和运行模型的类，GGUF 文件才是模型数据。
2. `self.llm` 从哪里来？
   - 它是 `LocalLLM` 自己定义的对象属性，保存 `Llama(...)` 创建的运行对象。
3. 为什么 `max_tokens` 不在加载模型时固定？
   - 它是每次生成的输出限制，可以随请求变化，因此在调用模型时传入。
4. `stop` 的作用是什么？
   - 当模型生成指定文本时提前停止，避免继续生成多余内容或下一轮角色标签。
5. `text` 是自己定义的吗？
   - 不是，它是 `llama_cpp` Completion 响应格式规定的字段。
6. 为什么 `system_prompt` 没有和 `user_input` 一起使用？
   - 当前保留 Lesson 01 的最简调用；Lesson 02 方法再负责拼接两类输入。
7. `if __name__ == "__main__"` 有什么作用？
   - 区分直接运行和被其他文件导入，避免导入时自动加载模型。
8. 两个 `assert` 测试了什么？
   - 测试模型返回值是非空字符串，但尚未测试回答内容是否正确。

## Stage 2 过程中遇到的问题

1. `raw_decode()` 是哪里来的？
   - 它来自 Python 标准库 `json` 中的 `JSONDecoder` 对象，用来从字符串开头解析出一个完整 JSON。
2. `parsed, _ = ...` 中 `_` 是什么？
   - `_` 是普通变量名，但常用来表示“不关心这个返回值”。当前只需要 `parsed`，不需要 JSON 结束位置。
3. `**kwargs` 是把 dict 变成什么？
   - 不是变成新数据类型，而是在函数调用时把字典拆成关键字参数，比如 `prompt=...`、`max_tokens=...`。
4. 函数必须用 `return` 结尾吗？
   - 不必须。没有 `return` 时默认返回 `None`。但需要给调用方结果时，应该明确写 `return`。
5. `None` 是否表示没有出错？
   - 不是。`None` 表示没有有效值，常用于表达失败、缺失、找不到、无法解析。
6. `join()` 是做什么？
   - 它把一组字符串用指定连接符拼成一个字符串。当前用于把 choices list 转成 prompt 中的多行选项。
7. schema 是否要写出所有可能数据？
   - 不需要。schema 只描述当前步骤需要返回给下一步 Python 使用的数据。
8. choices 是否要覆盖所有可能输出？
   - 不需要。choices 只用于封闭选择任务，例如工具路由。开放文本回答不应该被枚举。
9. prompt 里的 Python 数据为什么要转成字符串？
   - LLM 输入本质是文本，所以 list、dict、state、memory 都要整理成模型能读懂的 prompt。
10. `full_agent_practice.py` 报缩进错误怎么办？
    - Python 同一函数内部代码必须对齐。`prompt = ...` 和 `return ...` 都属于同一个函数体时，应保持同一缩进层级。

## Stage 3 过程中需要重点理解的问题

1. 工具函数是模型生成的吗？
   - 不是。工具函数由 Python 提前定义，例如 `calculator()`。
2. 模型生成的是什么？
   - 模型生成工具调用请求，例如 `{"tool": "calculator", "arguments": {...}}`。
3. `arguments` 是什么？
   - 它是传给工具函数的参数字典，后续通过 `**arguments` 拆成关键字参数。
4. `tools` 字典为什么能存函数？
   - Python 中函数也是对象，可以作为 value 存入字典。
5. 为什么要先测 `fixed_tool_call`？
   - 它不经过模型，能单独验证 Python 工具层是否正常。
6. 为什么工具名要校验？
   - 因为模型输出不可信，Python 只允许执行已经注册的工具。
7. Stage 3 和 MCP 像在哪里？
   - 思路类似：模型提出结构化工具请求，外部系统负责真实执行。但当前版本是本地 Python 函数，不是完整 MCP 协议。

## 当前边界

当前阶段已经验证：

- 本地模型能够加载。
- Prompt 能够发送给模型。
- 模型响应能够被提取为字符串。
- `SimpleAgent` 能够通过 `LocalLLM` 调用模型。
- `test.py` 中 Stage 2 的新增代码通过语法编译检查。
- `test.py` 中 Stage 3 的工具层通过非模型验证：`execute_tool("calculator", ...) == 294`。

当前阶段尚未实现：

- `full_agent_practice.py` 中 Stage 2 需要由学习者继续手敲、运行和调试。
- `full_agent_practice.py` 中 Stage 3 需要由学习者继续手敲、运行和调试。
- Agent Loop。
- State、Memory、Plan、Atomic Action、AoT。
- Telemetry 接入真实 Agent 流程。
- Golden Eval 和完整自动化测试。

## 后续路线

1. Stage 2：加入 `generate_with_role()`、`generate_structured()` 和 `decide()`。
2. Stage 3：加入工具注册、工具请求和工具执行。
3. Stage 4：加入 `AgentState`、循环和 Memory。
4. Stage 5：加入 Plan、Atomic Action 和 AoT 依赖图。
5. Stage 6：接入自写 Telemetry，记录 LLM、工具、记忆和错误 Span。
6. Stage 7：编写 Eval cases，验证决策、工具、记忆和失败路径。

## 复习问题

1. `Llama` 类、`self.llm` 对象和 GGUF 文件分别负责什么？
2. 为什么 `model_path` 属于初始化参数，而 `max_tokens` 属于生成参数？
3. `self.llm(**kwargs)` 实际展开后是什么样子？
4. 为什么当前 `simple_generate()` 没有使用 `system_prompt`？
5. 如果模型返回空字符串，哪一条断言会失败？
6. `schema` 和 `choices` 的区别是什么？
7. 为什么 LLM 输出 JSON 后还要 Python 再解析和校验？
8. `None`、`False`、空字符串和空字典的含义有什么区别？
9. 为什么封闭动作要限制选项，而开放回答不能枚举所有答案？
10. `dict → prompt 字符串 → LLM 输出字符串 → dict` 这条链路如何描述？
11. LLM 请求工具和 Python 执行工具分别发生在哪个函数里？
12. `tools[tool_name](**arguments)` 展开后是什么样子？
13. 如果 `fixed_tool_call` 成功但 `request_tool()` 失败，应该优先检查哪里？
14. 为什么不能直接相信模型输出的工具名？

## 本次提交建议

中文 commit message 可选：

```bash
git commit -m "练习：补充 Agent 工具调用参考实现"
```

如果这次只提交文档，不提交代码：

```bash
git commit -m "文档：记录完整 Agent 练习第三阶段"
```

如果同时提交 `test.py` 和学习笔记：

```bash
git commit -m "学习：整理 Agent 工具调用流程"
```
