import re
from typing import Optional, Dict
from datetime import datetime
from models.bytecode import BytecodeOperation, OperationType

class OperationParser:
    """Parser for individual bytecode operations"""
    
    def parse_operation(self, op_type: str, op_details: str) -> Optional[BytecodeOperation]:
        """Parse a single bytecode operation"""
        try:
            operation_type = OperationType(op_type)
            operation = BytecodeOperation(operation=operation_type)
            
            # Extract common metadata
            self._extract_metadata(operation, op_details)
            
            # Parse operation-specific details
            if operation_type == OperationType.ALLOC:
                self._parse_alloc(operation, op_details)
            elif operation_type in [OperationType.TRANSFER_HOST_TO_DEVICE, OperationType.TRANSFER_DEVICE_TO_HOST]:
                self._parse_transfer(operation, op_details)
            elif operation_type == OperationType.LAUNCH:
                self._parse_launch(operation, op_details)
            elif operation_type == OperationType.DEALLOC:
                self._parse_dealloc(operation, op_details)
            elif operation_type in [OperationType.ON_DEVICE, OperationType.ON_DEVICE_BUFFER]:
                self._parse_device_operation(operation, op_details)
            elif operation_type == OperationType.BARRIER:
                self._parse_barrier(operation, op_details)
                
            return operation
            
        except ValueError:
            # Unknown operation type
            return None
            
    def _extract_metadata(self, operation: BytecodeOperation, op_details: str) -> None:
        """Extract common metadata from operation details"""
        # Extract timestamp if available
        timestamp_match = re.search(r"\[timestamp=(\d+\.\d+)\]", op_details)
        if timestamp_match:
            operation.timestamp = float(timestamp_match.group(1))
            
        # Extract duration if available
        duration_match = re.search(r"\[duration=(\d+\.\d+)\]", op_details)
        if duration_match:
            operation.duration = float(duration_match.group(1))
            
        # Extract device and thread IDs if available
        device_match = re.search(r"\[device=(\w+)\]", op_details)
        if device_match:
            operation.device_id = device_match.group(1)
            
        thread_match = re.search(r"\[thread=(\w+)\]", op_details)
        if thread_match:
            operation.thread_id = thread_match.group(1)
            
    def _parse_alloc(self, operation: BytecodeOperation, op_details: str) -> None:
        """Parse ALLOC operation details"""
        obj_match = re.search(r"([\w\.]+@[0-9a-f]+) on\s+.*?, size=(\d+), batchSize=(\d+)", op_details)
        if obj_match:
            operation.objects.append(obj_match.group(1))
            operation.size = int(obj_match.group(2))
            operation.batch_size = int(obj_match.group(3))
            
    def _parse_transfer(self, operation: BytecodeOperation, op_details: str) -> None:
        """Parse TRANSFER operation details"""
        obj_match = re.search(r"\[(0x[0-9a-f]+|Object Hash Code=0x[0-9a-f]+)\] ([\w\.]+@[0-9a-f]+) on\s+.*?, size=(\d+), batchSize=(\d+)", op_details)
        if obj_match:
            operation.objects.append(obj_match.group(2))
            operation.size = int(obj_match.group(3))
            operation.batch_size = int(obj_match.group(4))
            
        # Extract event list if present
        event_match = re.search(r"\[event list=(-?\d+)\]", op_details)
        if event_match:
            operation.event_list = int(event_match.group(1))
            
    def _parse_launch(self, operation: BytecodeOperation, op_details: str) -> None:
        """Parse LAUNCH operation details"""
        task_match = re.search(r"task ([\w\.]+) - ([\w\.]+) on", op_details)
        if task_match:
            operation.task_name = task_match.group(1)
            
        # Extract event list if present
        event_match = re.search(r"\[event list=(\d+)\]", op_details)
        if event_match:
            operation.event_list = int(event_match.group(1))
            
    def _parse_dealloc(self, operation: BytecodeOperation, op_details: str) -> None:
        """Parse DEALLOC operation details"""
        obj_match = re.search(r"\[(0x[0-9a-f]+)\] ([\w\.]+@[0-9a-f]+) \[Status:\s+([\w\s]+)\]", op_details)
        if obj_match:
            operation.objects.append(obj_match.group(2))
            operation.status = obj_match.group(3).strip()
            
    def _parse_device_operation(self, operation: BytecodeOperation, op_details: str) -> None:
        """Parse ON_DEVICE or ON_DEVICE_BUFFER operation details"""
        obj_match = re.search(r"\[(0x[0-9a-f]+)\] ([\w\.]+@[0-9a-f]+)", op_details)
        if obj_match:
            operation.objects.append(obj_match.group(2))
            
    def _parse_barrier(self, operation: BytecodeOperation, op_details: str) -> None:
        """Parse BARRIER operation details"""
        event_match = re.search(r"event-list (\d+)", op_details)
        if event_match:
            operation.event_list = int(event_match.group(1))
