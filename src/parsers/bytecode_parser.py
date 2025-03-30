import re
from typing import List, Optional
from ..models.bytecode import BytecodeOperation
from ..models.task_graph import TaskGraph

class BytecodeParser:
    """Parser for TornadoVM bytecode logs"""
    
    def __init__(self):
        self.graphs: Dict[str, TaskGraph] = {}
        self.memory_objects: Dict[str, MemoryObject] = {}
        
    def parse_log(self, log_content: str) -> None:
        """Parse the entire log content"""
        # Split the log into sections for each task graph
        graph_sections = re.split(r'\[TASK GRAPH\]', log_content)[1:]  # Skip the first empty split
        
        for section in graph_sections:
            # Extract graph ID from the section
            graph_id_match = re.search(r'Graph ID: (\w+)', section)
            if not graph_id_match:
                continue
                
            graph_id = graph_id_match.group(1)
            self._parse_task_graph(section, graph_id)
            
    def _parse_task_graph(self, section: str, graph_id: str) -> None:
        """Parse a single task graph section"""
        # Extract device and thread information
        device_match = re.search(r'Device: (.+)', section)
        thread_match = re.search(r'Thread: (.+)', section)
        
        if not device_match or not thread_match:
            return
            
        device = device_match.group(1)
        thread = thread_match.group(1)
        
        # Create new task graph
        task_graph = TaskGraph(graph_id=graph_id, device=device, thread=thread)
        
        # Parse operations
        operation_sections = re.split(r'\[OPERATION\]', section)[1:]  # Skip the first empty split
        
        for op_section in operation_sections:
            operation = self._parse_operation(op_section)
            if operation:
                self._process_operation(operation, task_graph)
                
        self.graphs[graph_id] = task_graph
        
    def _parse_operation(self, op_section: str) -> Optional[BytecodeOperation]:
        """Parse a single operation section"""
        # Extract operation type
        op_type_match = re.search(r'Type: (\w+)', op_section)
        if not op_type_match:
            return None
            
        op_type = op_type_match.group(1)
        
        # Create operation object
        operation = BytecodeOperation(operation=op_type)
        
        # Extract object references
        objects_match = re.search(r'Objects: (.+)', op_section)
        if objects_match:
            operation.objects = [obj.strip() for obj in objects_match.group(1).split(',')]
            
        # Extract size information
        size_match = re.search(r'Size: (\d+)', op_section)
        if size_match:
            operation.size = int(size_match.group(1))
            
        # Extract batch size
        batch_match = re.search(r'Batch Size: (\d+)', op_section)
        if batch_match:
            operation.batch_size = int(batch_match.group(1))
            
        # Extract task name
        task_match = re.search(r'Task: (.+)', op_section)
        if task_match:
            operation.task_name = task_match.group(1)
            
        # Extract event list
        event_match = re.search(r'Event List: (\d+)', op_section)
        if event_match:
            operation.event_list = int(event_match.group(1))
            
        # Extract offset
        offset_match = re.search(r'Offset: (\d+)', op_section)
        if offset_match:
            operation.offset = int(offset_match.group(1))
            
        # Extract status for DEALLOC operations
        if op_type == 'DEALLOC':
            status_match = re.search(r'Status: (.+)', op_section)
            if status_match:
                operation.status = status_match.group(1)
                
        return operation
        
    def _process_operation(self, operation: BytecodeOperation, task_graph: TaskGraph) -> None:
        """Process a parsed operation and update the task graph"""
        task_graph.operations.append(operation)
        
        if operation.task_name:
            task_graph.tasks.append(operation.task_name)
            
        # Process object references
        for obj_ref in operation.objects:
            obj_hash = self._extract_hash(obj_ref)
            if not obj_hash:
                continue
                
            if operation.operation in ['ALLOC', 'TRANSFER_HOST_TO_DEVICE']:
                task_graph.objects_produced.add(obj_hash)
            else:
                task_graph.objects_consumed.add(obj_hash)
                
    def _extract_hash(self, obj_ref: str) -> Optional[str]:
        """Extract hash ID from object reference"""
        hash_match = re.search(r'@(\w+)', obj_ref)
        return hash_match.group(1) if hash_match else None
