from dataclasses import dataclass, field
from typing import List

@dataclass
class BytecodeOperation:
    """Represents a single bytecode operation"""
    operation: str  # e.g., ALLOC, TRANSFER_HOST_TO_DEVICE, etc.
    objects: List[str] = field(default_factory=list)  # Object references
    size: int = 0
    batch_size: int = 0
    task_name: str = ""
    event_list: int = -1
    offset: int = 0
    status: str = ""  # For DEALLOC status (Persisted/Freed)
