import plotly.graph_objects as go
from typing import Dict, Optional
from ..models.task_graph import TaskGraph
from ..models.memory_object import MemoryObject

class ObjectFlowVisualizer:
    """Visualizes object flow between task graphs"""
    
    def __init__(self, graphs: Dict[str, TaskGraph], memory_objects: Dict[str, MemoryObject]):
        self.graphs = graphs
        self.memory_objects = memory_objects
        
    def visualize(self, selected_object: Optional[str] = None) -> go.Figure:
        """Create an interactive object flow visualization"""
        # Create figure
        fig = go.Figure()
        
        # If no object selected, show all objects
        objects_to_show = [selected_object] if selected_object else self.memory_objects.keys()
        
        # Add traces for each object
        for obj_id in objects_to_show:
            if obj_id not in self.memory_objects:
                continue
                
            obj = self.memory_objects[obj_id]
            
            # Create nodes and edges for this object's flow
            nodes = []
            edges = []
            
            # Add allocation node
            if obj.allocation_op_index >= 0:
                nodes.append(dict(
                    id=f"{obj_id}_alloc",
                    label=f"Allocated in {obj.allocated_in_graph}",
                    color="green"
                ))
                
            # Add transfer nodes and edges
            for i, (transfer_type, graph_id, op_index) in enumerate(obj.transfer_history):
                node_id = f"{obj_id}_transfer_{i}"
                nodes.append(dict(
                    id=node_id,
                    label=f"Transferred ({transfer_type})",
                    color="blue"
                ))
                
                if i == 0 and obj.allocation_op_index >= 0:
                    edges.append(dict(
                        from_=f"{obj_id}_alloc",
                        to=node_id,
                        label=f"Graph: {graph_id}"
                    ))
                elif i > 0:
                    edges.append(dict(
                        from_=f"{obj_id}_transfer_{i-1}",
                        to=node_id,
                        label=f"Graph: {graph_id}"
                    ))
                    
            # Add deallocation node
            if obj.deallocation_op_index >= 0:
                dealloc_id = f"{obj_id}_dealloc"
                nodes.append(dict(
                    id=dealloc_id,
                    label=f"Deallocated ({obj.current_status})",
                    color="red"
                ))
                
                if obj.transfer_history:
                    edges.append(dict(
                        from_=f"{obj_id}_transfer_{len(obj.transfer_history)-1}",
                        to=dealloc_id,
                        label=f"Status: {obj.current_status}"
                    ))
                elif obj.allocation_op_index >= 0:
                    edges.append(dict(
                        from_=f"{obj_id}_alloc",
                        to=dealloc_id,
                        label=f"Status: {obj.current_status}"
                    ))
                    
            # Add object flow diagram
            fig.add_trace(go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=[node["label"] for node in nodes],
                    color=[node["color"] for node in nodes]
                ),
                link=dict(
                    source=[nodes.index(dict(id=edge["from"])) for edge in edges],
                    target=[nodes.index(dict(id=edge["to"])) for edge in edges],
                    value=[1] * len(edges),
                    label=[edge["label"] for edge in edges]
                )
            ))
            
        # Update layout
        fig.update_layout(
            title=f'Object Flow Visualization{f" for {selected_object}" if selected_object else ""}',
            font_size=10
        )
        
        return fig
