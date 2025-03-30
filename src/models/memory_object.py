from dataclasses import dataclass, field
from typing import List, Set, Tuple

@dataclass
class MemoryObject:
    """Tracks a memory object through its lifecycle"""
    object_id: str  # Hash ID
    object_type: str
    size: int = 0
    allocated_in_graph: str = ""
    current_status: str = "Unknown"  # Allocated, Transferred, Persisted, Freed
    allocation_op_index: int = -1
    deallocation_op_index: int = -1
    used_in_graphs: Set[str] = field(default_factory=set)
    transfer_history: List[Tuple[str, str, int]] = field(default_factory=list)  # (type, graph_id, op_index)
