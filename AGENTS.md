# Project Memory: Agent Study

## Learning Protocol

For every learning session in this repository, follow this fixed flow:

1. Read the matching lesson file first: `lessons/XX_*.md`.
2. Find the matching demo function in `complete_example.py`, such as `lesson_01_basic_chat()`.
3. Trace the corresponding implementation in `agent/agent.py`.
4. Follow helper calls only when needed:
   - `shared/llm.py` for local model loading and text generation.
   - `shared/utils.py` for JSON extraction and parsing helpers.
   - `agent/tools.py` for tool definitions and execution.
   - `agent/memory.py` for memory behavior.
   - `agent/planner.py` for planning, atomic actions, and AoT graphs.
   - `agent/evals.py` and `evals/golden_datasets.py` for evaluation.
   - `agent/telemetry.py` for runtime observability.
5. Run a focused example for the current lesson instead of running all of `complete_example.py`, unless the goal is full review.
6. End each lesson with four notes:
   - What capability was added?
   - Which code entrypoint implements it?
   - What belongs to the model, and what belongs to the agent wrapper?
   - What failure mode or open question did we observe?

## Teaching Style

Use a prediction-first learning rhythm:

1. Predict what the code will do.
2. Read the relevant code path.
3. Run the smallest useful example.
4. Compare the output with the prediction.
5. Summarize the mental model in plain Chinese.

Keep explanations focused on one concept at a time. Prefer short code traces over broad lectures.

## Project Boundaries

- Do not treat `.venv/` as source code; it is only the local Python environment.
- Do not treat `models/` or `*.gguf` files as source code; they are local model assets.
- Do not commit virtual environments, model files, or runtime telemetry.
- The expected local model path is `models/llama-3-8b-instruct.gguf`.
