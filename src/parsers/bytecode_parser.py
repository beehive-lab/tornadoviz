import re
from typing import List, Optional, Dict
from models.bytecode import BytecodeOperation
from models.task_graph import TaskGraph
from models.memory_object import MemoryObject

class BytecodeParser:
    """Parser for TornadoVM bytecode logs"""

    def __init__(self):
        self.graphs: Dict[str, TaskGraph] = {}
        self.memory_objects: Dict[str, MemoryObject] = {}
        self.bytecode_details: List[Dict] = []  # For detailed bytecode visualization
        
    def parse_log(self, log_content: str) -> None:
        """Parse the entire log content"""
        # Split by "Interpreter instance" lines to get each task graph
        sections = re.split(r'(?=Interpreter instance running bytecodes)', log_content)

        graph_id = 0
        for section in sections:
            if not section.strip():
                continue
            self._parse_task_graph(section, f"TaskGraph_{graph_id}")
            graph_id += 1

        # Build dependencies after all graphs are parsed
        self._build_dependencies()
            
    def _parse_task_graph(self, section: str, graph_id: str) -> None:
        """Parse a single task graph section"""
        # Extract device and thread from "Interpreter instance running bytecodes for: DEVICE Running in thread: THREAD"
        header_match = re.search(r'Interpreter instance running bytecodes for:\s+(.+?)\s+Running in thread:\s+(.+)', section)

        if not header_match:
            return

        device = header_match.group(1).strip()
        thread = header_match.group(2).strip()

        # Create new task graph
        task_graph = TaskGraph(graph_id=graph_id, device=device, thread=thread)

        # Parse bytecode operations - each line starting with "bc:"
        global_op_index = sum(len(g.operations) for g in self.graphs.values())
        lines = section.split('\n')
        for line in lines:
            if line.strip().startswith('bc:'):
                operation = self._parse_operation(line)
                if operation:
                    # Store bytecode details for visualization
                    op_details = line.replace('bc:', '').strip().split(None, 1)
                    details_str = op_details[1] if len(op_details) > 1 else ""

                    self.bytecode_details.append({
                        "TaskGraph": graph_id,
                        "Operation": operation.operation,
                        "Details": details_str,
                        "GlobalIndex": global_op_index,
                        "Objects": ", ".join(operation.objects),
                        "TaskName": operation.task_name if operation.task_name else ""
                    })
                    global_op_index += 1

                    self._process_operation(operation, task_graph)

        self.graphs[graph_id] = task_graph
        
    def _parse_operation(self, line: str) -> Optional[BytecodeOperation]:
        """Parse a single bytecode operation line"""
        # Remove "bc:" prefix and extra whitespace
        line = line.replace('bc:', '').strip()

        # Extract the operation type (first word)
        parts = line.split(None, 1)
        if not parts:
            return None

        op_type = parts[0].strip()
        op_details = parts[1] if len(parts) > 1 else ""

        # Create operation object
        operation = BytecodeOperation(operation=op_type)

        # Parse based on operation type for better accuracy
        if op_type == "ALLOC":
            obj_match = re.search(r"([\w\.]+@[0-9a-f]+) on\s+.*?, size=(\d+), batchSize=(\d+)", op_details)
            if obj_match:
                operation.objects.append(obj_match.group(1))
                operation.size = int(obj_match.group(2))
                operation.batch_size = int(obj_match.group(3))

        elif op_type.startswith("TRANSFER"):
            obj_match = re.search(r"\[(0x[0-9a-f]+|Object Hash Code=0x[0-9a-f]+)\] ([\w\.]+@[0-9a-f]+) on\s+.*?, size=(\d+), batchSize=(\d+)", op_details)
            if obj_match:
                operation.objects.append(obj_match.group(2))
                operation.size = int(obj_match.group(3))
                operation.batch_size = int(obj_match.group(4))

                event_match = re.search(r"\[event list=(-?\d+)\]", op_details)
                if event_match:
                    operation.event_list = int(event_match.group(1))

        elif op_type == "LAUNCH":
            # Extract task name - just use the main task name
            task_match = re.search(r"task ([\w\.]+) - ([\w\.]+) on", op_details)
            if task_match:
                operation.task_name = task_match.group(1)

                event_match = re.search(r"\[event list=(\d+)\]", op_details)
                if event_match:
                    operation.event_list = int(event_match.group(1))

        elif op_type == "DEALLOC":
            obj_match = re.search(r"\[(0x[0-9a-f]+)\] ([\w\.]+@[0-9a-f]+) \[Status:\s+([\w\s]+)\]", op_details)
            if obj_match:
                operation.objects.append(obj_match.group(2))
                operation.status = obj_match.group(3).strip()

        elif op_type == "ON_DEVICE_BUFFER" or op_type == "ON_DEVICE":
            obj_match = re.search(r"\[(0x[0-9a-f]+)\] ([\w\.]+@[0-9a-f]+)", op_details)
            if obj_match:
                operation.objects.append(obj_match.group(2))

        elif op_type == "BARRIER":
            event_match = re.search(r"event-list (\d+)", op_details)
            if event_match:
                operation.event_list = int(event_match.group(1))
        else:
            # Fallback: extract object references
            object_refs = re.findall(r'[\w.]+@\w+', line)
            operation.objects = object_refs

        return operation
        
    def _process_operation(self, operation: BytecodeOperation, task_graph: TaskGraph) -> None:
        """Process a parsed operation and update the task graph"""
        op_index = len(task_graph.operations)
        task_graph.operations.append(operation)

        if operation.task_name:
            task_graph.tasks.append(operation.task_name)

        # Process object references
        for obj_ref in operation.objects:
            obj_hash = self._extract_hash(obj_ref)
            if not obj_hash:
                continue

            # Track memory objects
            if obj_hash not in self.memory_objects:
                self.memory_objects[obj_hash] = MemoryObject(
                    object_id=obj_hash,
                    object_type=self._extract_type(obj_ref)
                )

            mem_obj = self.memory_objects[obj_hash]
            mem_obj.used_in_graphs.add(task_graph.graph_id)

            # Handle different operations
            if operation.operation == 'ALLOC':
                task_graph.objects_produced.add(obj_hash)
                mem_obj.allocated_in_graph = task_graph.graph_id
                mem_obj.allocation_op_index = op_index
                mem_obj.current_status = 'Allocated'
                if operation.size > 0:
                    mem_obj.size = operation.size

            elif operation.operation.startswith('TRANSFER'):
                task_graph.objects_produced.add(obj_hash)
                mem_obj.transfer_history.append((operation.operation, task_graph.graph_id, op_index))
                mem_obj.current_status = 'Transferred'
                if operation.size > 0:
                    mem_obj.size = operation.size

            elif operation.operation == 'DEALLOC':
                mem_obj.deallocation_op_index = op_index
                mem_obj.current_status = operation.status if operation.status else 'Freed'

            elif operation.operation == 'ON_DEVICE_BUFFER':
                task_graph.objects_consumed.add(obj_hash)
                mem_obj.current_status = 'On Device'

            else:
                task_graph.objects_consumed.add(obj_hash)
                
    def _extract_hash(self, obj_ref: str) -> Optional[str]:
        """Extract hash ID from object reference"""
        hash_match = re.search(r'@(\w+)', obj_ref)
        return hash_match.group(1) if hash_match else None

    def _extract_type(self, obj_ref: str) -> str:
        """Extract meaningful type name from object reference"""
        # Handle format with colon (e.g. rmsnorm:@hash)
        if ':' in obj_ref:
            return obj_ref.split(':')[0]

        # Extract the type part before the @ symbol
        type_part = obj_ref.split('@')[0] if '@' in obj_ref else obj_ref

        # Look for the last meaningful component in the package path
        components = type_part.split('.')

        # Special handling for known Tornado types
        for component in reversed(components):
            # Arrays (ByteArray, IntArray, FloatArray, etc)
            if component.endswith('Array'):
                return component

            # Vectors (VectorFloat, VectorInt, etc)
            if component.startswith('Vector'):
                return component

            # Matrices (Matrix2DFloat, Matrix3DInt, etc)
            if component.startswith('Matrix'):
                return component

            # Tensors (TensorInt32, TensorFP32, etc)
            if component.startswith('Tensor'):
                return component

            # KernelContext and other special types
            if component in ['KernelContext', 'TornadoCollectionInterface', 'TornadoMatrixInterface']:
                return component

        # If no specific type is found, return the last component
        return components[-1] if components else 'Unknown'

    def _build_dependencies(self) -> None:
        """Build dependencies between task graphs based on object usage"""
        # For each graph, check if it consumes objects produced by previous graphs
        graph_list = list(self.graphs.values())

        for i, graph in enumerate(graph_list):
            # Check consumed objects
            for obj_hash in graph.objects_consumed:
                # Find which previous graph produced this object
                for j in range(i):
                    prev_graph = graph_list[j]
                    if obj_hash in prev_graph.objects_produced:
                        # Add dependency
                        if prev_graph.graph_id not in graph.dependencies:
                            graph.dependencies[prev_graph.graph_id] = []
                        if obj_hash not in graph.dependencies[prev_graph.graph_id]:
                            graph.dependencies[prev_graph.graph_id].append(obj_hash)
