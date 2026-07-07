import json
import time

from dataclasses import asdict,dataclass
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4


@dataclass
class Span:
    span_id: str
    trace_id: str
    event_type: str
    timestamp: str
    duration_ms:float
    data:dict
    error: str | None = None

    def to_dict(self):
        return asdict(self)
    

@dataclass
class Metrics:
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_duration_ms: float = 0.0

    def success_rate(self):
        if self.total_operations == 0:
            return 0.0
        
        return (
            self.successful_operations
            / self.total_operations
            * 100
        )
    
    def to_dict(self):
        return {
            "total_operations": self.total_operations,
            "successful_operations": self.successful_operations,
            "failed_operations": self.failed_operations,
            "total_duration_ms": self.total_duration_ms,
            "success_rate": self.success_rate(),
        }


class Telemetry:
    def __init__(self,log_file):
        self.log_file = Path(log_file)
        self.current_trace_id = None
        self.spans = []
        self.metrics = Metrics()

    def start_trace(self):
        self.current_trace_id = str(uuid4())
        return self.current_trace_id
    
    def save_span(self,span):
        self.spans.append(span)

        with self.log_file.open(
            "a",
            encoding="utf-8",
        ) as file:
            json_line = json.dumps(
                span.to_dict(),
                ensure_ascii=False,
            )

            file.write(json_line + "\n")

    def track_operation(
        self,
        event_type,
        operation,
        data=None,
    ):
        if self.current_trace_id is None:
            self.start_trace()

        span_id = str(uuid4())

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        start_time = time.perf_counter()

        result = None
        error = None

        try:
            result = operation()
            return result
        
        except Exception as exception:
            error = (
                f"{type(exception).__name__}:"
                f"{exception}"
            )

            raise

        finally:
            end_time = time.perf_counter()

            duration_ms = (
                end_time - start_time
            ) * 1000

            span_data = dict(data or {})

            span_data["success"] = error is None
            span_data["result"] = result

            span = Span(
                span_id = span_id,
                trace_id=self.current_trace_id,
                event_type=event_type,
                timestamp=timestamp,
                duration_ms=duration_ms,
                data=span_data,
                error=error,
            )

            self.save_span(span)

            self.metrics.total_operations += 1
            self.metrics.total_duration_ms +=duration_ms

            if error is None:
                self.metrics.successful_operations += 1
            else:
                self.metrics.failed_operations +=1

    def clear(self):
        self.spans = []
        self.metrics = Metrics()

        if self.log_file.exists():
            self.log_file.unlink()

    def print_summary(self):
        print("\nTELEMETRY SUMMARY")
        print("=" * 40)

        print(
            json.dumps(
                self.metrics.to_dict(),
                indent=2,
                ensure_ascii=False,
            )
        )

    
def fake_llm_call():
    time.sleep(0.2)

    return(
        "An AI agent observes, decides, "
        "and takes actions."
    )


def calculator_tool():
    time.sleep(0.1)
    return 42 * 7


def broken_tool():
    time.sleep(0.05)
    return 10 / 0


telemetry = Telemetry(
      "lesson_12_telemetry.jsonl"
)

telemetry.clear()

trace_id = telemetry.start_trace()

print("Trace ID:", trace_id)


llm_result = telemetry.track_operation(
    event_type="llm_call",
    operation=fake_llm_call,
    data={
        "prompt": "What is an AI agent?",
    },
)

print("LLM result:", llm_result)


tool_result = telemetry.track_operation(
    event_type="tool_call",
    operation=calculator_tool,
    data={
        "tool": "calculator",
        "arguments": {
            "a": 42,
            "b": 7,
            "operation": "multiply",
        },
    },
)

print("Tool result:", tool_result)


try:
    telemetry.track_operation(
        event_type="tool_call",
        operation=broken_tool,
        data={
            "tool": "broken_tool",
        },
    )

except ZeroDivisionError:
    print("Broken tool failed, but telemetry recorded it.")


telemetry.print_summary()

print("\nSaved spans:")

for span in telemetry.spans:
    print(span.to_dict())
    