import pandas as pd
from typing import Dict, List
from ..models.task_graph import TaskGraph

class PerformanceAnalyzer:
    """Analyzes performance metrics from task graphs"""
    
    def __init__(self, graphs: Dict[str, TaskGraph]):
        self.graphs = graphs
        
    def get_task_summary(self) -> pd.DataFrame:
        """Generate a summary of task execution patterns"""
        task_data = []
        
        for graph_id, graph in self.graphs.items():
            for task_name in set(graph.tasks):
                task_ops = [op for op in graph.operations if op.task_name == task_name]
                
                task_data.append({
                    'Graph': graph_id,
                    'Task': task_name,
                    'Operation Count': len(task_ops),
                    'Device': graph.device,
                    'Thread': graph.thread,
                    'Operations': ', '.join(set(op.operation for op in task_ops))
                })
                
        return pd.DataFrame(task_data)
        
    def get_operation_timing(self) -> pd.DataFrame:
        """Analyze operation timing patterns"""
        timing_data = []
        
        for graph_id, graph in self.graphs.items():
            for i, op in enumerate(graph.operations):
                timing_data.append({
                    'Graph': graph_id,
                    'Operation': op.operation,
                    'Task': op.task_name,
                    'Index': i,
                    'Device': graph.device,
                    'Thread': graph.thread
                })
                
        return pd.DataFrame(timing_data)
        
    def get_device_utilization(self) -> pd.DataFrame:
        """Analyze device utilization patterns"""
        device_data = []
        
        for graph_id, graph in self.graphs.items():
            device_data.append({
                'Device': graph.device,
                'Thread': graph.thread,
                'Operation Count': len(graph.operations),
                'Unique Tasks': len(set(graph.tasks))
            })
            
        return pd.DataFrame(device_data)
