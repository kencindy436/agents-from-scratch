# Stage 4C Tool Feedback Loop Design

## Status

Accepted for implementation on 2026-07-10.

## Goal

Turn the Stage 4B decision-only loop into a minimal executable feedback loop:

```text
user input -> decision -> tool call -> tool result -> observation
-> final answer -> done
```

The acceptance task is `What is 42 * 7?`, with a calculator observation of
`294` and a final answer grounded in that observation.

## Learning Goal

After Stage 4C, the learner should be able to explain:

1. The difference between an action proposal and an executed action.
2. Why tool execution belongs to Python rather than the model.
3. What an observation is and why it must be fed into the next step.
4. Why Python, not the model, controls reliable termination.
5. How one task produces multiple linked result dictionaries.

## Decision

Keep the Stage 4B methods unchanged and add a parallel tool-aware loop. This
makes the two stages directly comparable:

```text
Stage 4B: agent_step() -> run_loop()
Stage 4C: tool_agent_step() -> run_tool_loop()
```

Stage 4C remains calculator-focused. A generic ReAct engine and arbitrary tool
schemas are deferred until the learner understands the feedback path.

## Alternatives Considered

### Modify the existing Stage 4B loop

- Advantage: fewer methods.
- Rejected: removes the clean comparison with the decision-only loop and mixes
  two learning stages.

### Add a parallel tool-aware loop (selected)

- Advantage: isolates execution and observation while reusing the existing
  routing, tool-request, and calculator functions.
- Cost: introduces two additional public learning methods.

### Build a generic ReAct engine

- Advantage: scales to many tools and action types.
- Rejected: adds dynamic schemas, general dispatch, observation formatting,
  retries, and recovery before the minimal data flow is mastered.

## State Changes

Extend `AgentState` with:

```python
self.observations = []
self.final_answer = None
```

`reset()` clears both values. `to_dict()` exposes them for debugging and future
prompts.

An observation is a Python dictionary produced after actual tool execution:

```python
{
    "tool": "calculator",
    "arguments": {
        "a": 42,
        "b": 7,
        "operation": "multiply",
    },
    "result": 294,
}
```

## Components

### `answer_from_observation(user_input, observation)`

Build a prompt containing the original request and the trusted Python tool
observation. Ask the model for a concise final answer that uses the exact tool
result. Return a string.

### `tool_agent_step(user_input)`

The method behaves as a two-phase state machine.

#### Phase 1: no observation exists

1. Route between `use_tool` and `answer_question`.
2. For `use_tool`, ask the model for a calculator request.
3. Validate and execute the request in Python.
4. Store the tool, arguments, and result as an observation.
5. Return an action dictionary with `action == "use_tool"`.

For `answer_question`, generate a direct answer, save it as `final_answer`, mark
the state done, and return an action dictionary with
`action == "final_answer"`.

#### Phase 2: an observation exists

1. Read the latest observation.
2. Call `answer_from_observation()`.
3. Save the returned text as `final_answer`.
4. Save the final action as `last_action`.
5. Increment `steps` and mark the state done.
6. Return an action dictionary with `action == "final_answer"`.

### `run_tool_loop(user_input, max_steps=3)`

1. Reset state.
2. Repeatedly call `tool_agent_step()`.
3. Append every returned step to `results`.
4. Stop when `state.done` is true or `max_steps` is reached.
5. Return the result list.

## Expected Data Flow

```text
What is 42 * 7?
        |
        v
decision: use_tool
        |
        v
tool_call: calculator(42, 7, multiply)
        |
        v
Python result: 294
        |
        v
state.observations.append(...)
        |
        v
model reads original request + observation
        |
        v
final answer containing 294
        |
        v
state.done = True
```

## Responsibility Boundary

The model is responsible for:

- choosing the route from allowed choices;
- producing calculator arguments;
- turning a trusted observation into natural-language output.

Python is responsible for:

- validating model output;
- executing the calculator;
- creating and storing observations;
- counting successful steps;
- recording the final answer;
- marking completion;
- enforcing `max_steps`;
- recording errors.

## Error Handling

Every failure becomes an inspectable action dictionary:

```python
{
    "action": "error",
    "error": "description",
}
```

The error step is stored as `last_action`, increments `steps`, marks the task
done, and is returned to `run_tool_loop()`. This prevents silent termination and
makes failures visible in `results`.

The following failures are handled:

- no valid route after retries;
- no valid tool request after retries;
- unknown tool or invalid arguments;
- tool execution exception;
- empty final answer.

## Verification Strategy

Deterministic checks use scripted LLM responses:

1. `{"decision": "use_tool"}`
2. a valid calculator request for `42 * 7`
3. `42 multiplied by 7 is 294.`

Expected deterministic assertions:

- exactly two result steps;
- first action is `use_tool`;
- first observation result is `294`;
- second action is `final_answer`;
- final answer contains `294`;
- `state.steps == 2`;
- `state.done is True`;
- `state.final_answer` matches the second result.

The model-backed example asserts stable properties only. It does not require an
exact sentence, but the final answer must contain `294`.

## Scope Boundary

Stage 4C does not include:

- web search or file-system tools;
- arbitrary tool schemas;
- multiple tool calls in one task;
- long-term memory;
- planning or dependency graphs;
- telemetry or golden eval suites.

After Stage 4C, the next learning stage is Memory: preserving selected
information across separate calls rather than only within one task loop.
