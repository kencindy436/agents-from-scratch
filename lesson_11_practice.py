from agent.agent import Agent


DECISION_GOLDEN = [
    {
        "input": "Can you summarize this article for me?",
        "choices": ["answer_question", "summarize_text", "translate"],
        "expected": "summarize_text",
    },
    {
        "input": "Translate hello to Spanish",
        "choices": ["answer_question", "summarize_text", "translate"],
        "expected": "translate",
    },
]

def evaluate_decisions(agent,cases):
    results = []
    passed_count = 0
    failed_count = 0

    for case in cases:
        actual = agent.decide(
            case["input"],
            case["choices"],
        )

        error = None

        if actual is None:
            error = "no decisions made"
        elif actual != case["expected"]:
            error = "wrong decision"

        passed = error is None

        result = {
            "passed": passed,
            "input": case["input"],
            "expected": case["expected"],
            "actual":actual,
            "error":error,
        }

        results.append(result)

        if passed:
            passed_count += 1
        else:
            failed_count += 1

    return {
        "passed": passed_count,
        "failed": failed_count,
        "results": results,
    }

def print_report(report):
    print("\nDECISION EVAL REPORT")
    print("=" * 40)

    for result in report["results"]:
        status = "passed" if result["passed"] else "failed"

        print(f"\n{status}")
        print("Input:", result["input"])
        print("Expected:", result["expected"])
        print("Actual:", result["actual"])

        if result["error"]:
            print("Error:",result["error"])

    print("\n" + "-" * 40)
    print("Passed:", report["passed"])
    print("Failed:", report["failed"])

agent = Agent("models/llama-3-8b-instruct.gguf")

report = evaluate_decisions(
    agent,
    DECISION_GOLDEN,
)

print_report(report)