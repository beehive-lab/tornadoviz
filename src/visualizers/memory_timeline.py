import plotly.graph_objects as go
from typing import Dict, List
from ..models.task_graph import TaskGraph
from ..models.memory_object import MemoryObject

class MemoryTimelineVisualizer:
    """Visualizes memory operations over time"""
    
    def __init__(self, graphs: Dict[str, TaskGraph], memory_objects: Dict[str, MemoryObject]):
        self.graphs = graphs
        self.memory_objects = memory_objects
        
    def visualize(self) -> go.Figure:
        """Create an interactive memory timeline visualization"""
        # Create figure
        fig = go.Figure()
        
        # Add traces for each memory object
        for obj_id, obj in self.memory_objects.items():
            # Create timeline of operations
            operations = []
            timestamps = []
            
            # Add allocation operation
            if obj.allocation_op_index >= 0:
                operations.append("Allocated")
                timestamps.append(obj.allocation_op_index)
                
            # Add transfer operations
            for transfer_type, graph_id, op_index in obj.transfer_history:
                operations.append(f"Transferred ({transfer_type})")
                timestamps.append(op_index)
                
            # Add deallocation operation
            if obj.deallocation_op_index >= 0:
                operations.append("Deallocated")
                timestamps.append(obj.deallocation_op_index)
                
            # Add trace for this object
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=[obj_id] * len(timestamps),
                mode='markers+lines+text',
                name=obj_id,
                text=operations,
                textposition="top center",
                marker=dict(
                    size=10,
                    color=[self._get_operation_color(op) for op in operations]
                )
            ))
            
        # Update layout
        fig.update_layout(
            title='Memory Object Timeline',
            xaxis_title='Operation Index',
            yaxis_title='Object ID',
            showlegend=True,
            hovermode='closest'
        )
        
        return fig
        
    def _get_operation_color(self, operation: str) -> str:
        """Get color for different operation types"""
        if "Allocated" in operation:
            return "green"
        elif "Transferred" in operation:
            return "blue"
        elif "Deallocated" in operation:
            return "red"
        return "gray"
