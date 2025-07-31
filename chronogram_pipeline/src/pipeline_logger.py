from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional

from .logger import get_logger

@dataclass
class StepMetrics:
    name: str
    start: datetime = field(default_factory=datetime.now)
    end: Optional[datetime] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

    def stop(self) -> None:
        self.end = datetime.now()

    @property
    def duration(self) -> float:
        if not self.end:
            return 0.0
        return (self.end - self.start).total_seconds()


class _StepContext:
    def __init__(self, pipeline_logger: "PipelineLogger", name: str):
        self.pipeline_logger = pipeline_logger
        self.step = StepMetrics(name)

    def __enter__(self) -> Dict[str, Any]:
        self.pipeline_logger.logger.info(
            f"START_{self.step.name}",
            extra={"event": "STEP_START", "step": self.step.name},
        )
        return self.step.metrics

    def __exit__(self, exc_type, exc, tb) -> None:
        self.step.stop()
        data = {
            "event": "STEP_END",
            "step": self.step.name,
            "duration": self.step.duration,
            **self.step.metrics,
        }
        if exc_type is not None:
            self.pipeline_logger.success = False
            data["error"] = str(exc)
            self.pipeline_logger.logger.error(f"ERROR_{self.step.name}", extra=data)
        else:
            self.pipeline_logger.logger.info(f"END_{self.step.name}", extra=data)
        self.pipeline_logger.steps.append(self.step)


class PipelineLogger:
    """Helper to log pipeline steps with metrics and summary."""

    def __init__(self, name: str = "chronopipeline") -> None:
        self.logger = get_logger(name)
        self.start = datetime.now()
        self.steps: List[StepMetrics] = []
        self.success = True

    def step(self, name: str) -> _StepContext:
        return _StepContext(self, name)

    def summary(self) -> None:
        total = (datetime.now() - self.start).total_seconds()
        summary_steps = []
        for st in self.steps:
            entry = {"name": st.name, "duration": st.duration}
            entry.update(st.metrics)
            summary_steps.append(entry)
        self.logger.info(
            "SUMMARY",
            extra={
                "event": "SUMMARY",
                "status": "SUCCES" if self.success else "ECHEC",
                "total_duration": total,
                "steps": summary_steps,
            },
        )

