# Stage 4B Agent Loop Design

## Status

Accepted for implementation on 2026-07-10.

## Goal

Upgrade the Stage 4A one-shot router into a minimal multi-step agent loop that
can inspect state, choose an action, update state, repeat, and stop safely.

## Learning Goal

After completing this stage, the learner should be able to explain:

1. Why `run()` is only one `observe -> decide -> act` cycle.
2. What data belongs in `AgentState`.
3. What one agent step means.
4. Why `run_loop()` needs both `done` and `max_steps` termination conditions.
5. Which outputs come from the model and which state changes are performed by
   Python.

## Decision

Implement the source-aligned minimal loop first. Stage 4B will add state and
repetition, but it will not execute real tools. Connecting calculator execution
to the loop is deferred to Stage 4C.

## Alternatives Considered

### Minimal source-aligned loop (selected)

- Adds `AgentState`, `agent_step()`, and `run_loop()`.
- Makes the loop and state transitions easy to inspect.
- Matches Lesson 06 in the repository.
- Actions are proposals returned by the model, not real side effects.

### Tool-executing loop (deferred)

- Would connect the Stage 4A calculator to every loop iteration.
- Is closer to a practical agent, but mixes routing, state, tool execution,
  observations, and error handling in one learning step.

## Components

### `AgentState`

The state object owns:

- `steps`: number of successfully parsed agent actions.
- `done`: whether the agent has selected the `done` action.
- `last_action`: the latest valid action dictionary, or `None` before any step.

It exposes:

- `increment_step()`
- `mark_done()`
- `reset()`
- `to_dict()`

### `SimpleAgent.__init__()`

Create one state object when an agent is initialized:

```python
self.state = AgentState()
```

### `agent_step(user_input)`

One step performs this sequence:

1. Read the current state with `self.state.to_dict()`.
2. Put the state and user input into the prompt.
3. Ask the model for one JSON action.
4. Parse and validate the response.
5. Save the action as `last_action`.
6. Increment `steps`.
7. Return the action dictionary.

The allowed actions are `analyze`, `research`, `summarize`, `answer`, and
`done`. A valid model response has this shape:

```json
{
  "action": "analyze",
  "reason": "First understand the user's goal"
}
```

### `run_loop(user_input, max_steps=5)`

The loop performs this sequence:

1. Reset state at the beginning of a new task.
2. Create an empty `results` list.
3. Continue while `done` is false and `steps` is below `max_steps`.
4. Call `agent_step()`.
5. Append a valid action to `results`.
6. Mark the state done if the model selected `done`.
7. Break if a valid action cannot be produced.
8. Return all collected actions.

## Data Flow

```text
user_input + current state
          |
          v
      agent_step()
          |
          v
      prompt text
          |
          v
         LLM
          |
          v
raw response string
          |
          v
extract_json_from_text()
          |
          v
validated action dict
          |
          +--> update AgentState
          |
          +--> append to results
          |
          v
repeat or stop
```

## Responsibility Boundary

The model is responsible for generating values such as:

- `action`
- `reason`

Python is responsible for:

- parsing JSON;
- checking that the action is allowed;
- counting steps;
- storing `last_action`;
- marking `done`;
- enforcing `max_steps`;
- collecting and returning results.

## Failure Handling

- Retry invalid model output up to three times.
- Return `None` from `agent_step()` if all attempts fail.
- Stop `run_loop()` when `agent_step()` returns `None`.
- Always enforce `max_steps` to prevent an infinite loop.

## Verification Strategy

Deterministic checks that do not load the model:

- new state starts with `steps == 0` and `done is False`;
- `increment_step()` changes `steps` from 0 to 1;
- `mark_done()` changes `done` to `True`;
- `reset()` restores the initial values;
- `to_dict()` returns the expected dictionary.

Model-backed checks:

- `run_loop(..., max_steps=3)` returns a list;
- the result length never exceeds 3;
- every result is a dictionary with an allowed `action`;
- final state `steps` equals the number of valid returned actions;
- the loop stops after `done`, invalid output, or the step limit.

Exact action sequences are not asserted because local LLM output is
probabilistic and may repeat actions.

## Scope Boundary

Stage 4B does not include:

- real execution of `research`, `summarize`, or `answer` actions;
- calculator calls inside the loop;
- feeding an action result back as a new observation;
- persistent memory;
- planning or dependency graphs;
- telemetry.

Those capabilities will be layered on after the minimal loop is understood.
