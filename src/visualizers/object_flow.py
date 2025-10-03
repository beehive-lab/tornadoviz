import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Optional
from models.task_graph import TaskGraph
from models.memory_object import MemoryObject

class ObjectFlowVisualizer:
    """Visualizes object flow between task graphs"""

    def __init__(self, graphs: Dict[str, TaskGraph], memory_objects: Dict[str, MemoryObject]):
        self.graphs = graphs
        self.memory_objects = memory_objects

    def visualize(self, selected_object: Optional[str] = None) -> go.Figure:
        """Visualize the flow of a specific object through task graphs"""
        if not selected_object and self.memory_objects:
            # Choose the first object if none specified
            selected_object = next(iter(self.memory_objects.keys()))

        if not selected_object or selected_object not in self.memory_objects:
            return go.Figure()

        obj = self.memory_objects[selected_object]
        obj_type = self._extract_type(obj.object_type)
        short_id = f"{obj_type}@{obj.object_id[:8]}"

        # Prepare data
        events = []

        # Add allocation event
        alloc_graph = obj.allocated_in_graph
        events.append({
            "TaskGraph": alloc_graph,
            "Event": "Allocated",
            "Size": obj.size,
            "EventIndex": obj.allocation_op_index,
            "GlobalIndex": sum(len(g.operations) for g_id, g in self.graphs.items()
                              if g_id < alloc_graph) + obj.allocation_op_index
        })

        # Add transfer events
        for transfer_type, graph_id, op_index in obj.transfer_history:
            global_index = sum(len(g.operations) for g_id, g in self.graphs.items()
                              if g_id < graph_id) + op_index
            events.append({
                "TaskGraph": graph_id,
                "Event": transfer_type,
                "Size": obj.size,
                "EventIndex": op_index,
                "GlobalIndex": global_index
            })

        # Add deallocation event if present
        if obj.deallocation_op_index >= 0:
            dealloc_graph = None
            for graph_id, graph in self.graphs.items():
                if obj.object_id in [self._extract_hash(obj_ref) for op in graph.operations
                                    for obj_ref in op.objects if op.operation == "DEALLOC"]:
                    dealloc_graph = graph_id
                    break

            if dealloc_graph:
                global_index = sum(len(g.operations) for g_id, g in self.graphs.items()
                                  if g_id < dealloc_graph) + obj.deallocation_op_index
                events.append({
                    "TaskGraph": dealloc_graph,
                    "Event": f"Deallocated ({obj.current_status})",
                    "Size": obj.size,
                    "EventIndex": obj.deallocation_op_index,
                    "GlobalIndex": global_index
                })

        df = pd.DataFrame(events)
        if df.empty:
            return go.Figure()

        # Create enhanced flow visualization
        fig = go.Figure()

        # Color mapping for events
        color_map = {
            "Allocated": "#22c55e",  # Green
            "TRANSFER_HOST_TO_DEVICE_ONCE": "#3b82f6",  # Blue
            "TRANSFER_HOST_TO_DEVICE_ALWAYS": "#1d4ed8",  # Dark blue
            "TRANSFER_DEVICE_TO_HOST_ALWAYS": "#8b5cf6",  # Purple
        }

        # Add line connecting events
        fig.add_trace(go.Scatter(
            x=df["TaskGraph"],
            y=[1] * len(df),
            mode="lines",
            line=dict(color="rgba(255,255,255,0.3)", width=3),
            hoverinfo="none",
            showlegend=False
        ))

        # Add markers for each event
        for _, row in df.iterrows():
            event_type = row["Event"]
            if event_type.startswith("Deallocated"):
                color = "#ef4444"  # Red
                symbol = "x"
                size = 20  # Increased marker size
            else:
                color = color_map.get(event_type, "gray")
                symbol = "circle"
                size = 20  # Increased marker size

            fig.add_trace(go.Scatter(
                x=[row["TaskGraph"]],
                y=[1],
                mode="markers",
                marker=dict(
                    color=color,
                    size=size,
                    symbol=symbol,
                    line=dict(width=2, color='black')  # Increased line width
                ),
                name=event_type,
                text=f"<b>{event_type}</b> in {row['TaskGraph']}<br>Size: {row['Size']:,} bytes",
                hoverinfo="text"
            ))

        # Update layout
        fig.update_layout(
            title={
                'text': f"Object Flow: {short_id}",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 20}
            },
            xaxis_title="Task Graph",
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)',
                tickangle=-45,  # Rotate labels for better readability
                tickfont=dict(size=14),  # Increased tick font size
                tickmode='array',  # Force all task graph names to show
                ticktext=df["TaskGraph"].unique(),
                tickvals=df["TaskGraph"].unique()
            ),
            yaxis=dict(
                showticklabels=False,
                zeroline=False,
                showgrid=False,
                range=[0.5, 1.5]  # Adjusted range for better marker visibility
            ),
            hovermode="closest",
            height=200,  # Reduced height since we only have one line
            width=1200,  # Increased width for better spacing
            template="plotly_white",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=50, r=150, t=80, b=120),  # Increased margins, especially bottom and right
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=1.1,  # Moved legend further right
                bgcolor='rgba(0,0,0,0)',
                font=dict(size=14)
            ),
            font=dict(
                color='white',
                size=14
            )
        )

        return fig

    def _extract_hash(self, obj_ref: str) -> str:
        """Extract hash from object reference"""
        import re
        match = re.search(r"@([0-9a-f]+)", obj_ref)
        return match.group(1) if match else obj_ref

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
        return components[-1]
