# Full Agent Practice 学习笔记

## 当前状态

- 日期：2026-07-07
- 练习代码：`/Users/cuiyuqi/agent/full_agent_practice.py`
- 当前阶段：Stage 1 已完成
- 验证结果：本地 GGUF 模型能够成功加载，并返回非空字符串

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

## 当前边界

当前阶段已经验证：

- 本地模型能够加载。
- Prompt 能够发送给模型。
- 模型响应能够被提取为字符串。
- `SimpleAgent` 能够通过 `LocalLLM` 调用模型。

当前阶段尚未实现：

- System Prompt 拼接。
- JSON 提取、校验与重试。
- 决策、工具调用和 Agent Loop。
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
