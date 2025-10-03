import pandas as pd
from typing import Dict, List
from collections import defaultdict
from models.task_graph import TaskGraph

class PerformanceAnalyzer:
    """Analyzes performance metrics from task graphs"""

    def __init__(self, graphs: Dict[str, TaskGraph], memory_objects: Dict = None):
        self.graphs = graphs
        self.memory_objects = memory_objects or {}
        
    def get_task_summary(self) -> pd.DataFrame:
        """Generate a summary of task execution patterns"""
        task_data = []

        for graph_id, graph in self.graphs.items():
            if not graph.tasks:
                continue
            for task_name in set(graph.tasks):
                task_ops = [op for op in graph.operations if op.task_name == task_name]

                task_data.append({
                    'Graph': graph_id,
                    'Task': task_name,
                    'Operation Count': len(task_ops),
                    'Device': graph.device,
                    'Thread': graph.thread,
                    'Operations': ', '.join(sorted(set(op.operation for op in task_ops)))
                })

        if not task_data:
            return pd.DataFrame(columns=['Graph', 'Task', 'Operation Count', 'Device', 'Thread', 'Operations'])

        return pd.DataFrame(task_data)
        
    def get_operation_timing(self) -> pd.DataFrame:
        """Analyze operation timing patterns"""
        timing_data = []

        for graph_id, graph in self.graphs.items():
            for i, op in enumerate(graph.operations):
                timing_data.append({
                    'Graph': graph_id,
                    'Operation': op.operation,
                    'Task': op.task_name if op.task_name else 'N/A',
                    'Index': i,
                    'Device': graph.device,
                    'Thread': graph.thread
                })

        if not timing_data:
            return pd.DataFrame(columns=['Graph', 'Operation', 'Task', 'Index', 'Device', 'Thread'])

        return pd.DataFrame(timing_data)
        
    def get_device_utilization(self) -> pd.DataFrame:
        """Analyze device utilization patterns"""
        device_data = []

        for graph_id, graph in self.graphs.items():
            device_data.append({
                'Graph': graph_id,
                'Device': graph.device,
                'Thread': graph.thread,
                'Operation Count': len(graph.operations),
                'Unique Tasks': len(set(graph.tasks))
            })

        if not device_data:
            return pd.DataFrame(columns=['Graph', 'Device', 'Thread', 'Operation Count', 'Unique Tasks'])

        return pd.DataFrame(device_data)

    def generate_task_summary(self) -> pd.DataFrame:
        """Generate a summary of tasks and memory operations"""
        task_data = []

        for graph_id, graph in self.graphs.items():
            # Base metrics for the graph
            num_allocs = sum(1 for op in graph.operations if op.operation == "ALLOC")
            num_transfers = sum(1 for op in graph.operations
                               if op.operation.startswith("TRANSFER"))
            num_deallocs = sum(1 for op in graph.operations if op.operation == "DEALLOC")
            num_persisted = sum(1 for op in graph.operations
                               if op.operation == "DEALLOC" and "Persisted" in op.status)

            # Calculate total memory allocated/transferred
            mem_allocated = sum(op.size for op in graph.operations if op.operation == "ALLOC")
            mem_transferred = sum(op.size for op in graph.operations
                                if op.operation.startswith("TRANSFER"))

            # Get exact object dependencies with simplified formatting
            dep_details = []
            for dep_graph, obj_hashes in graph.dependencies.items():
                obj_details = []
                for obj_hash in obj_hashes:
                    if obj_hash in self.memory_objects:
                        obj = self.memory_objects[obj_hash]
                        # Format as TYPE@HASH
                        if ':' in obj.object_type:
                            type_name = obj.object_type.split(':')[0]
                        elif '.' in obj.object_type:
                            parts = obj.object_type.split('.')
                            meaningful_parts = [p for p in parts if p not in ['uk', 'ac', 'manchester', 'tornado', 'api', 'types']]
                            type_name = meaningful_parts[-1] if meaningful_parts else obj.object_type
                        else:
                            type_name = obj.object_type
                        obj_details.append(f"{type_name}@{obj_hash}")
                if obj_details:
                    dep_details.append(f"{', '.join(obj_details)}")

            # Track operations per task
            task_operations = defaultdict(list)
            current_task = None
            task_execution_order = []

            for op in graph.operations:
                if op.operation == "LAUNCH" and op.task_name:
                    current_task = op.task_name
                    if current_task not in task_execution_order:
                        task_execution_order.append(current_task)
                if current_task:
                    task_operations[current_task].append(op)
                else:
                    # Operations before first task are associated with graph setup
                    task_operations[f"{graph_id}_setup"].append(op)

            # If no explicit tasks found, create a default task
            if not task_operations:
                task_operations[f"{graph_id}_main"] = graph.operations
                task_execution_order = [f"{graph_id}_main"]
            elif f"{graph_id}_setup" in task_operations:
                task_execution_order.insert(0, f"{graph_id}_setup")

            # Create entries for the graph and its tasks
            # First, add the graph summary
            task_data.append({
                "TaskGraph": graph_id,
                "Task": f"📊 {graph_id} (Total Operations: {len(graph.operations)})",
                "Device": graph.device,
                "Allocations": num_allocs,
                "Deallocations": num_deallocs,
                "PersistedObjects": num_persisted,
                "TotalMemoryAllocated (MB)": f"{mem_allocated/(1024*1024):.2f}",
                "TotalMemoryTransferred (MB)": f"{mem_transferred/(1024*1024):.2f}",
                "Dependencies": "\n".join(dep_details) if dep_details else "None",
                "NumOperations": len(graph.operations)
            })

            # Then add each task with its operations
            for task_name in task_execution_order:
                ops = task_operations[task_name]
                op_counts = defaultdict(int)
                for op in ops:
                    op_counts[op.operation] += 1

                # Format operation counts
                op_summary = ", ".join(f"{op}: {count}" for op, count in op_counts.items())

                task_data.append({
                    "TaskGraph": graph_id,
                    "Task": f"↳ {task_name} ({len(ops)} ops)",
                    "Device": graph.device,
                    "Allocations": sum(1 for op in ops if op.operation == "ALLOC"),
                    "Deallocations": sum(1 for op in ops if op.operation == "DEALLOC"),
                    "PersistedObjects": sum(1 for op in ops if op.operation == "DEALLOC" and "Persisted" in op.status),
                    "TotalMemoryAllocated (MB)": f"{sum(op.size for op in ops if op.operation == 'ALLOC')/(1024*1024):.2f}",
                    "TotalMemoryTransferred (MB)": f"{sum(op.size for op in ops if op.operation.startswith('TRANSFER'))/(1024*1024):.2f}",
                    "Dependencies": op_summary,
                    "NumOperations": len(ops)
                })

        # Create DataFrame and ensure it's not empty
        df = pd.DataFrame(task_data)
        if df.empty:
            # Create a dummy row if no data
            df = pd.DataFrame([{
                "TaskGraph": "No Data",
                "Task": "No Tasks Found",
                "Device": "N/A",
                "Allocations": 0,
                "Deallocations": 0,
                "PersistedObjects": 0,
                "TotalMemoryAllocated (MB)": "0.00",
                "TotalMemoryTransferred (MB)": "0.00",
                "Dependencies": "None",
                "NumOperations": 0
            }])

        return df
