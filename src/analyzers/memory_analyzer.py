import pandas as pd
from typing import Dict
from ..models.task_graph import TaskGraph
from ..models.memory_object import MemoryObject

class MemoryAnalyzer:
    """Analyzes memory usage patterns"""
    
    def __init__(self, graphs: Dict[str, TaskGraph], memory_objects: Dict[str, MemoryObject]):
        self.graphs = graphs
        self.memory_objects = memory_objects
        
    def get_memory_usage(self) -> pd.DataFrame:
        """Generate memory usage statistics"""
        usage_data = []
        
        for obj_id, obj in self.memory_objects.items():
            usage_data.append({
                'Object ID': obj_id,
                'Type': obj.object_type,
                'Size': obj.size,
                'Allocation Graph': obj.allocated_in_graph,
                'Status': obj.current_status,
                'Used in Graphs': ', '.join(obj.used_in_graphs)
            })
            
        return pd.DataFrame(usage_data)
        
    def get_object_persistence(self) -> pd.DataFrame:
        """Analyze object persistence patterns"""
        persistence_data = []
        
        for obj_id, obj in self.memory_objects.items():
            persistence_data.append({
                'Object ID': obj_id,
                'Type': obj.object_type,
                'Status': obj.current_status,
                'Transfer Count': len(obj.transfer_history),
                'Graphs Used': len(obj.used_in_graphs)
            })
            
        return pd.DataFrame(persistence_data)
        
    def get_graph_memory_usage(self) -> pd.DataFrame:
        """Analyze memory usage per graph"""
        graph_data = []
        
        for graph_id, graph in self.graphs.items():
            # Calculate total memory allocated in this graph
            total_memory = sum(
                obj.size for obj in self.memory_objects.values()
                if obj.allocated_in_graph == graph_id
            )
            
            # Count objects allocated in this graph
            allocated_objects = sum(
                1 for obj in self.memory_objects.values()
                if obj.allocated_in_graph == graph_id
            )
            
            graph_data.append({
                'Graph': graph_id,
                'Device': graph.device,
                'Thread': graph.thread,
                'Total Memory (bytes)': total_memory,
                'Allocated Objects': allocated_objects
            })
            
        return pd.DataFrame(graph_data)
