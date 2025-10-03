import pandas as pd
from typing import Dict, List
from models.task_graph import TaskGraph

class TaskAnalyzer:
    """Analyzes task execution patterns"""
    
    def __init__(self, graphs: Dict[str, TaskGraph]):
        self.graphs = graphs
        
    def get_task_dependencies(self) -> pd.DataFrame:
        """Analyze task dependencies between graphs"""
        dependency_data = []

        for graph_id, graph in self.graphs.items():
            for dep_graph_id, objects in graph.dependencies.items():
                dependency_data.append({
                    'Graph': graph_id,
                    'Dependent Graph': dep_graph_id,
                    'Shared Objects': len(objects),
                    'Device': graph.device,
                    'Thread': graph.thread
                })

        if not dependency_data:
            return pd.DataFrame(columns=['Graph', 'Dependent Graph', 'Shared Objects', 'Device', 'Thread'])

        return pd.DataFrame(dependency_data)
        
    def get_task_sequence(self) -> pd.DataFrame:
        """Analyze task execution sequence"""
        sequence_data = []

        for graph_id, graph in self.graphs.items():
            for i, task_name in enumerate(graph.tasks):
                sequence_data.append({
                    'Graph': graph_id,
                    'Task': task_name,
                    'Sequence': i,
                    'Device': graph.device,
                    'Thread': graph.thread
                })

        if not sequence_data:
            return pd.DataFrame(columns=['Graph', 'Task', 'Sequence', 'Device', 'Thread'])

        return pd.DataFrame(sequence_data)
        
    def get_task_operation_distribution(self) -> pd.DataFrame:
        """Analyze distribution of operations across tasks"""
        distribution_data = []

        for graph_id, graph in self.graphs.items():
            if not graph.tasks:
                continue
            for task_name in set(graph.tasks):
                task_ops = [op for op in graph.operations if op.task_name == task_name]
                op_counts = {}

                for op in task_ops:
                    op_counts[op.operation] = op_counts.get(op.operation, 0) + 1

                for op_type, count in sorted(op_counts.items()):
                    distribution_data.append({
                        'Graph': graph_id,
                        'Task': task_name,
                        'Operation': op_type,
                        'Count': count,
                        'Device': graph.device,
                        'Thread': graph.thread
                    })

        if not distribution_data:
            return pd.DataFrame(columns=['Graph', 'Task', 'Operation', 'Count', 'Device', 'Thread'])

        return pd.DataFrame(distribution_data)
