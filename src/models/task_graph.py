from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from collections import defaultdict
from datetime import datetime
from models.bytecode import BytecodeOperation

@dataclass
class TaskMetrics:
    """Metrics for a single task"""
    name: str
    operation_count: int = 0
    memory_allocated: int = 0
    memory_transferred: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    device_utilization: float = 0.0
    operation_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

@dataclass
class TaskGraph:
    """Represents a TornadoVM task graph"""
    graph_id: str  # Extracted from the log
    device: str
    thread: str
    operations: List[BytecodeOperation] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))  # Graph -> [objects]
    objects_produced: Set[str] = field(default_factory=set)  # Objects created or modified
    objects_consumed: Set[str] = field(default_factory=set)  # Objects used but not created
    tasks: List[str] = field(default_factory=list)  # Named tasks in this graph
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    task_metrics: Dict[str, TaskMetrics] = field(default_factory=dict)
    metadata: Dict[str, str] = field(default_factory=dict)  # Additional graph metadata
    performance_metrics: Dict[str, float] = field(default_factory=dict)  # Performance-related metrics
    error_count: int = 0
    warning_count: int = 0
    critical_path: List[str] = field(default_factory=list)  # Critical path of task execution
    resource_usage: Dict[str, float] = field(default_factory=dict)  # Resource usage metrics
