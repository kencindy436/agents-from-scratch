# Stage 4C Tool Feedback Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use test-driven-development and execute each task in order. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a calculator-backed feedback loop that executes a real tool, stores its result as an observation, generates a grounded final answer, and terminates reliably.

**Architecture:** Preserve the Stage 4B methods and add `answer_from_observation()`, `tool_agent_step()`, and `run_tool_loop()`. Extend `AgentState` with observations and a final answer. Keep deterministic scripted-LLM checks and the model-backed example in `/Users/cuiyuqi/agent/test.py`.

**Tech Stack:** Python 3.12, `llama-cpp-python`, standard-library `json`, plain `assert` checks.

---

### Task 1: Extend Agent State

**Files:**
- Modify: `/Users/cuiyuqi/agent/test.py`

- [ ] **Step 1: Run a failing state check**

Run an import-only assertion that expects `observations` and `final_answer` on a new `AgentState`.

Expected: FAIL because the attributes do not exist.

- [ ] **Step 2: Add state fields**

Add to `AgentState.__init__()`:

```python
self.observations = []
self.final_answer = None
```

Reset both fields in `reset()` and include them in `to_dict()`:

```python
"observations": self.observations.copy(),
"final_answer": self.final_answer,
```

- [ ] **Step 3: Verify state behavior**

Assert initial values, mutation, dictionary conversion, and reset behavior.

Expected: PASS.

### Task 2: Generate an Answer From an Observation

**Files:**
- Modify: `/Users/cuiyuqi/agent/test.py`

- [ ] **Step 1: Run a failing method check**

Assert that `SimpleAgent.answer_from_observation` exists.

Expected: FAIL because the method is missing.

- [ ] **Step 2: Add the method**

Add:

```python
def answer_from_observation(self, user_input, observation):
    prompt = f"""{self.system_prompt}

Answer the original user request using the trusted tool observation below.
Use the exact tool result. Do not recalculate or change it.

Original user request: {user_input}
Tool observation: {observation}

Final answer:"""

    return self.llm.generate(
        prompt,
        temperature=0.0,
    )
```

- [ ] **Step 3: Verify observation propagation**

Use a capturing scripted LLM and assert that the prompt includes both the user request and `294`.

Expected: PASS.

### Task 3: Add One Tool-Aware Agent Step

**Files:**
- Modify: `/Users/cuiyuqi/agent/test.py`

- [ ] **Step 1: Run a failing method check**

Assert that `SimpleAgent.tool_agent_step` exists.

Expected: FAIL because the method is missing.

- [ ] **Step 2: Add the observation phase**

When `self.state.observations` is non-empty, read the latest observation,
generate the final answer, store it, increment the step, mark done, and return:

```python
{
    "action": "final_answer",
    "answer": answer,
}
```

If the answer is empty, return an `error` step and mark done.

- [ ] **Step 3: Add the initial routing phase**

When no observation exists, call:

```python
decision = self.decide(
    user_input,
    ["answer_question", "use_tool"],
)
```

For `answer_question`, generate a direct final answer and mark done.

For `use_tool`, request and execute the calculator, then store:

```python
observation = {
    "tool": tool_call["tool"],
    "arguments": tool_call["arguments"],
    "result": tool_result,
}
```

Return:

```python
{
    "action": "use_tool",
    "tool_call": tool_call,
    "observation": observation,
}
```

- [ ] **Step 4: Add explicit error steps**

For routing failure, invalid tool request, tool execution exception, or empty
answer, construct:

```python
{
    "action": "error",
    "error": "specific message",
}
```

Save it to `last_action`, increment the step, mark done, and return it.

- [ ] **Step 5: Verify individual phases**

Use scripted LLM responses to assert:

- a valid tool step stores observation result `294` without marking done;
- a following observation step returns a final answer and marks done;
- invalid calculator arguments produce an inspectable error step.

### Task 4: Add the Tool Feedback Loop

**Files:**
- Modify: `/Users/cuiyuqi/agent/test.py`

- [ ] **Step 1: Run a failing method check**

Assert that `SimpleAgent.run_tool_loop` exists.

Expected: FAIL because the method is missing.

- [ ] **Step 2: Add the loop**

Add:

```python
def run_tool_loop(self, user_input, max_steps=3):
    self.state.reset()
    results = []

    while (
        not self.state.done
        and self.state.steps < max_steps
    ):
        step_result = self.tool_agent_step(user_input)

        if step_result is None:
            break

        results.append(step_result)

    return results
```

- [ ] **Step 3: Add deterministic checks inside `test.py`**

Define `run_stage_4c_deterministic_checks()` after `SimpleAgent`. Inside it,
define a `ScriptedLLM`, create a `SimpleAgent` instance with `object.__new__()`
to avoid loading the GGUF model, and assert:

```python
assert len(results) == 2
assert results[0]["action"] == "use_tool"
assert results[0]["observation"]["result"] == 294
assert results[1]["action"] == "final_answer"
assert "294" in results[1]["answer"]
assert agent.state.steps == 2
assert agent.state.done is True
assert agent.state.final_answer == results[1]["answer"]
```

Add checks for an invalid route and invalid calculator arguments.

- [ ] **Step 4: Run deterministic checks**

Run the check function without constructing `Llama`.

Expected output: `Stage 4C deterministic checks passed`.

### Task 5: Add the Real-Model Acceptance Example

**Files:**
- Modify: `/Users/cuiyuqi/agent/test.py`

- [ ] **Step 1: Call deterministic checks first**

At the start of the main block:

```python
run_stage_4c_deterministic_checks()
```

- [ ] **Step 2: Add the model-backed tool loop**

After existing Stage 4B assertions, run:

```python
tool_loop_results = agent.run_tool_loop(
    "What is 42 * 7?",
    max_steps=3,
)
```

Assert two steps, the calculator observation `294`, final-answer action, final
answer containing `294`, `steps == 2`, and `done is True`.

- [ ] **Step 3: Print the feedback flow**

Print each Stage 4C result and the final state so the learner can distinguish
the tool observation from the final natural-language answer.

- [ ] **Step 4: Verify without loading the model**

Run `py_compile` and the deterministic check function.

Expected: zero exit status and the deterministic success message.

- [ ] **Step 5: Learner runs the real model**

Run:

```bash
cd /Users/cuiyuqi/agent
source .venv/bin/activate
python test.py
```

Expected Stage 4C properties: calculator result `294`, a final answer containing
`294`, two steps, and final state `done == True`.
