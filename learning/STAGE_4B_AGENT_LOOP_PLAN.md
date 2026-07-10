# Stage 4B Agent Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use test-driven-development and execute each task in order.

**Goal:** Add a minimal stateful multi-step agent loop to the reference `test.py` while preserving `full_agent_practice.py` for learner hand-typing.

**Architecture:** `AgentState` owns mutable loop state. `SimpleAgent.agent_step()` asks the LLM for one validated action and updates state. `SimpleAgent.run_loop()` repeats steps until `done`, invalid output, or `max_steps`.

**Tech Stack:** Python 3.12, `llama-cpp-python`, standard-library `json`, plain `assert` checks.

---

### Task 1: Add `AgentState`

**Files:**
- Modify: `/Users/cuiyuqi/agent/test.py`

- [ ] Run a failing import check that expects `test.AgentState` to exist.
- [ ] Add `AgentState` before `LocalLLM` with `steps`, `done`, `last_action`, `increment_step()`, `mark_done()`, `reset()`, and `to_dict()`.
- [ ] Run deterministic assertions for initial state, increment, completion, dictionary conversion, and reset.

### Task 2: Add one agent step

**Files:**
- Modify: `/Users/cuiyuqi/agent/test.py`

- [ ] Run a failing check that expects `SimpleAgent.agent_step` to exist.
- [ ] Initialize `self.state = AgentState()` in `SimpleAgent.__init__()`.
- [ ] Add `agent_step(user_input)` with allowed actions, a state-aware JSON prompt, three retries, validation, a default reason, and state updates.
- [ ] Use a scripted LLM response to verify that one valid action increments `steps` and sets `last_action`.

### Task 3: Add the multi-step loop

**Files:**
- Modify: `/Users/cuiyuqi/agent/test.py`

- [ ] Run a failing check that expects `SimpleAgent.run_loop` to exist.
- [ ] Add `run_loop(user_input, max_steps=5)` with reset, result accumulation, `done` termination, invalid-output termination, and the safety limit.
- [ ] Use scripted `analyze` then `done` responses to verify two results, `steps == 2`, and `done is True`.
- [ ] Use repeated `analyze` responses to verify that `max_steps=3` limits the loop to three actions.

### Task 4: Add learner-facing runtime checks

**Files:**
- Modify: `/Users/cuiyuqi/agent/test.py`
- Modify later by learner: `/Users/cuiyuqi/agent/full_agent_practice.py`

- [ ] Add a model-backed `run_loop(..., max_steps=3)` example under `if __name__ == "__main__":`.
- [ ] Assert only stable properties: list type, maximum length, allowed action names, and state/result count agreement.
- [ ] Print every iteration and the final state for inspection.
- [ ] Run `py_compile` and deterministic checks without loading the model.
- [ ] Let the learner run the full model-backed script and compare the output with the documented data flow.
