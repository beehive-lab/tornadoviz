import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from typing import Dict, List
from models.task_graph import TaskGraph
from models.memory_object import MemoryObject

class MemoryTimelineVisualizer:
    """Visualizes memory operations over time"""

    def __init__(self, graphs: Dict[str, TaskGraph], memory_objects: Dict[str, MemoryObject]):
        self.graphs = graphs
        self.memory_objects = memory_objects

    def visualize(self) -> go.Figure:
        """Create an enhanced interactive timeline of memory operations"""
        # Prepare data
        operations = []
        taskgraph_boundaries = []  # Track where each taskgraph starts and ends
        current_index = 0

        for i, (graph_id, graph) in enumerate(self.graphs.items()):
            # Record taskgraph boundary
            start_index = current_index

            for j, op in enumerate(graph.operations):
                if op.operation in ["ALLOC", "TRANSFER_HOST_TO_DEVICE_ONCE", "TRANSFER_HOST_TO_DEVICE_ALWAYS",
                                  "TRANSFER_DEVICE_TO_HOST_ALWAYS", "DEALLOC", "ON_DEVICE", "ON_DEVICE_BUFFER"]:
                    for obj_ref in op.objects:
                        obj_hash = self._extract_hash(obj_ref)
                        if obj_hash in self.memory_objects:
                            obj = self.memory_objects[obj_hash]
                            obj_type = self._extract_type(obj.object_type)
                            display_name = f"{obj_type}@{obj_hash[:8]}"
                        else:
                            # If not in memory_objects, extract type directly from reference
                            obj_type = self._extract_type(obj_ref)
                            display_name = f"{obj_type}@{obj_hash[:8]}"

                        operations.append({
                            "TaskGraph": graph_id,
                            "Operation": op.operation,
                            "Object": display_name,
                            "ObjectType": obj_type,
                            "Size": op.size if hasattr(op, 'size') else 0,
                            "OperationIndex": current_index,
                            "Status": op.status if hasattr(op, 'status') else ""
                        })
                current_index += 1

            # Record taskgraph boundary
            taskgraph_boundaries.append({
                'graph_id': graph_id,
                'start': start_index,
                'end': current_index - 1
            })

        df = pd.DataFrame(operations)
        if df.empty:
            return go.Figure()

        # Sort objects by type and hash to ensure consistent ordering
        if not df.empty:
            df['SortKey'] = df['Object'].apply(lambda x: (x.split('@')[0], x.split('@')[1]))
            df = df.sort_values('SortKey')
            df = df.drop('SortKey', axis=1)

        # Create a more sophisticated timeline
        fig = go.Figure()

        # Color mapping for operations
        color_map = {
            "ALLOC": "#22c55e",  # Green
            "TRANSFER_HOST_TO_DEVICE_ONCE": "#3b82f6",  # Blue
            "TRANSFER_HOST_TO_DEVICE_ALWAYS": "#1d4ed8",  # Dark blue
            "TRANSFER_DEVICE_TO_HOST_ALWAYS": "#8b5cf6",  # Purple
            "DEALLOC": "#ef4444",  # Red
            "ON_DEVICE": "#f97316",  # Orange
            "ON_DEVICE_BUFFER": "#fb923c"  # Light orange
        }

        # Add description of the visualization
        st.markdown("""
        This timeline shows memory operations across different task graphs:
        - **Vertical lines** separate different task graphs
        - **Colored dots** represent different memory operations:
            - 🟢 Green: Memory allocations
            - 🔵 Blue: Host-to-device transfers
            - 🟣 Purple: Device-to-host transfers
            - 🔴 Red: Memory deallocations
            - 🟠 Orange: Device buffer operations
        - **Size of dots** indicates the amount of memory involved
        """)

        # Add vertical lines for taskgraph boundaries
        for boundary in taskgraph_boundaries:
            # Add vertical line at the start of each taskgraph
            fig.add_vline(
                x=boundary['start'],
                line_dash="dash",
                line_color="rgba(255, 255, 255, 0.3)",
                line_width=2,  # Made line thicker
                annotation_text=boundary['graph_id'],
                annotation_position="top",
                annotation=dict(
                    font_size=16,
                    font_color="white",
                    textangle=-15  # Reduced rotation angle
                )
            )

        # Add traces for each operation type
        for op_type, color in color_map.items():
            df_filtered = df[df["Operation"] == op_type]
            if not df_filtered.empty:

                size_ref = df_filtered["Size"].max()
                size_ref = size_ref if size_ref > 0 else 1
                sizes = df_filtered["Size"].apply(
                    lambda x: max(10, min(25, 10 + (x / size_ref) * 15))
                )

# Size mapping for markers - make it proportional to data size but with min/max constraints
#                 size_ref = df_filtered["Size"].max() if not df_filtered.empty else 1
#                 sizes = df_filtered["Size"].apply(lambda x: max(10, min(25, 10 + (x / size_ref) * 15)))  # Increased marker sizes

                fig.add_trace(go.Scatter(
                    x=df_filtered["OperationIndex"],
                    y=df_filtered["Object"],
                    mode="markers",
                    marker=dict(
                        color=color,
                        size=sizes,
                        line=dict(width=1, color='DarkSlateGrey')
                    ),
                    name=op_type,
                    text=df_filtered.apply(
                        lambda row: f"<b>{row['Operation']}</b> in {row['TaskGraph']}<br>"
                                   f"Object: {row['Object']}<br>"
                                   f"Size: {row['Size']:,} bytes" +
                                   (f"<br>Status: {row['Status']}" if row['Status'] else ""),
                        axis=1
                    ),
                    hoverinfo="text"
                ))

        # Calculate dynamic height based on number of objects
        num_objects = len(df['Object'].unique())
        dynamic_height = max(600, min(1200, 400 + num_objects * 30))

        # Update layout
        fig.update_layout(
            title={
                'text': "Memory Objects Lifecycle",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 30}  # Increased from 28
            },
            xaxis_title={
                'text': "TaskGraph Sequence",
                'font': {'size': 22}  # Increased from 20
            },
            yaxis_title={
                'text': "Memory Objects",
                'font': {'size': 22}  # Increased from 20
            },
            height=dynamic_height,
            template="plotly_white",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(
                color='white',
                size=18  # Increased from 16
            ),
            xaxis=dict(
                gridcolor='rgba(128,128,128,0.2)',
                zerolinecolor='rgba(128,128,128,0.2)',
                showticklabels=True,
                tickmode='array',
                ticktext=[b['graph_id'] for b in taskgraph_boundaries],
                tickvals=[(b['start'] + b['end'])/2 for b in taskgraph_boundaries],
                tickangle=0,
                tickfont=dict(size=18)  # Increased from 16
            ),
            yaxis=dict(
                gridcolor='rgba(128,128,128,0.2)',
                zerolinecolor='rgba(128,128,128,0.2)',
                tickfont=dict(size=18)  # Increased from 16
            ),
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.05,
                bgcolor='rgba(0,0,0,0)',
                font=dict(size=18)  # Increased from 16
            ),
            hoverlabel=dict(
                font_size=18  # Increased from 16
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
