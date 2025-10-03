import pandas as pd
import plotly.graph_objects as go
from typing import Dict
from collections import defaultdict
from models.task_graph import TaskGraph
from models.memory_object import MemoryObject
import re

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
                'Size (bytes)': obj.size,
                'Allocation Graph': obj.allocated_in_graph,
                'Status': obj.current_status,
                'Used in Graphs': ', '.join(sorted(obj.used_in_graphs))
            })

        if not usage_data:
            return pd.DataFrame(columns=['Object ID', 'Type', 'Size (bytes)', 'Allocation Graph', 'Status', 'Used in Graphs'])

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

        if not persistence_data:
            return pd.DataFrame(columns=['Object ID', 'Type', 'Status', 'Transfer Count', 'Graphs Used'])

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

        if not graph_data:
            return pd.DataFrame(columns=['Graph', 'Device', 'Thread', 'Total Memory (bytes)', 'Allocated Objects'])

        return pd.DataFrame(graph_data)

    def get_memory_usage_chart(self) -> go.Figure:
        """Generate a chart showing memory usage over time"""
        # Track memory allocations and deallocations over time
        memory_events = []
        task_boundaries = []  # Track task boundaries
        taskgraph_boundaries = []  # Track taskgraph boundaries
        current_index = 0

        for i, (graph_id, graph) in enumerate(self.graphs.items()):
            # Record taskgraph boundary
            taskgraph_boundaries.append({
                'index': current_index,
                'name': graph_id
            })

            # Track tasks in this graph
            current_task = None
            for j, op in enumerate(graph.operations):
                if op.operation == "LAUNCH" and op.task_name:
                    current_task = op.task_name
                    task_boundaries.append({
                        'index': current_index + j,
                        'name': op.task_name,
                        'graph': graph_id
                    })

                if op.operation == "ALLOC":
                    for obj_ref in op.objects:
                        obj_hash = self._extract_hash(obj_ref)
                        memory_events.append({
                            "GlobalIndex": current_index + j,
                            "TaskGraph": graph_id,
                            "Task": current_task,
                            "Operation": "Allocation",
                            "Size": op.size,
                            "Object": obj_hash
                        })

                elif op.operation == "DEALLOC":
                    for obj_ref in op.objects:
                        obj_hash = self._extract_hash(obj_ref)
                        # Only count as deallocation if actually freed
                        if "Freed" in op.status:
                            memory_events.append({
                                "GlobalIndex": current_index + j,
                                "TaskGraph": graph_id,
                                "Task": current_task,
                                "Operation": "Deallocation",
                                "Size": -1 * self._get_object_size(obj_hash),  # Negative size for deallocation
                                "Object": obj_hash
                            })

            current_index += len(graph.operations)

        # Convert to DataFrame
        df = pd.DataFrame(memory_events)
        if df.empty:
            fig = go.Figure()
            fig.update_layout(
                title="Memory Usage Over Time (No Data)",
                xaxis_title="Operation Sequence",
                yaxis_title="Memory Usage (bytes)",
            )
            return fig

        # Calculate cumulative memory usage
        df = df.sort_values("GlobalIndex")
        df["CumulativeMemory"] = df["Size"].cumsum()

        # Create the chart
        fig = go.Figure()

        # Add memory usage line
        fig.add_trace(go.Scatter(
            x=df["GlobalIndex"],
            y=df["CumulativeMemory"],
            mode="lines",
            name="Memory Usage",
            line=dict(color="rgba(52, 152, 219, 1)", width=3),
            fill="tozeroy",
            fillcolor="rgba(52, 152, 219, 0.2)"
        ))

        # Add markers for allocation events
        allocs = df[df["Operation"] == "Allocation"]
        if not allocs.empty:
            fig.add_trace(go.Scatter(
                x=allocs["GlobalIndex"],
                y=allocs["CumulativeMemory"],
                mode="markers",
                marker=dict(color="green", size=8, symbol="circle"),
                name="Allocations",
                text=allocs.apply(
                    lambda row: f"Allocated {row['Size']:,} bytes<br>Object: {row['Object']}<br>In {row['TaskGraph']}" +
                              (f"<br>Task: {row['Task']}" if row['Task'] else ""),
                    axis=1
                ),
                hoverinfo="text"
            ))

        # Add markers for deallocation events
        deallocs = df[df["Operation"] == "Deallocation"]
        if not deallocs.empty:
            fig.add_trace(go.Scatter(
                x=deallocs["GlobalIndex"],
                y=deallocs["CumulativeMemory"],
                mode="markers",
                marker=dict(color="red", size=8, symbol="x"),
                name="Deallocations",
                text=deallocs.apply(
                    lambda row: f"Deallocated {abs(row['Size']):,} bytes<br>Object: {row['Object']}<br>In {row['TaskGraph']}" +
                              (f"<br>Task: {row['Task']}" if row['Task'] else ""),
                    axis=1
                ),
                hoverinfo="text"
            ))

        # Add vertical lines for taskgraph boundaries
        for boundary in taskgraph_boundaries[1:]:  # Skip first boundary
            fig.add_vline(
                x=boundary['index'],
                line_dash="dash",
                line_color="rgba(255, 255, 255, 0.3)",
                line_width=2,
                annotation_text=boundary['name'],
                annotation_position="top",
                annotation=dict(
                    font_size=16,
                    font_color="white",
                    textangle=-15
                )
            )

        # Update layout
        fig.update_layout(
            title={
                'text': "Memory Usage Over Time",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 20}
            },
            xaxis=dict(
                showticklabels=False,
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)',
                zeroline=False
            ),
            yaxis_title={
                'text': "Memory Usage (bytes)",
                'font': {'size': 16}
            },
            hovermode="closest",
            height=400,
            width=600,
            template="plotly_white",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(
                color='white',
                size=14
            ),
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=1,
                bgcolor='rgba(0,0,0,0)',
                font=dict(size=14)
            )
        )

        return fig

    def get_object_persistence_chart(self) -> go.Figure:
        """Create a chart showing object persistence patterns"""
        # Group objects by their status
        status_counts = defaultdict(int)

        for obj_hash, obj in self.memory_objects.items():
            status = obj.current_status
            status_counts[status] += 1

        # Convert to DataFrames
        count_df = pd.DataFrame({
            "Status": list(status_counts.keys()),
            "Count": list(status_counts.values())
        })

        if count_df.empty:
            fig = go.Figure()
            fig.update_layout(
                title="Object Persistence Analysis (No Data)",
                height=400,
                width=600
            )
            return fig

        # Create pie chart
        fig = go.Figure()

        fig.add_trace(go.Pie(
            labels=count_df["Status"],
            values=count_df["Count"],
            hole=0.4,
            textinfo="label+percent",
            hoverinfo="label+value+percent"
        ))

        # Update layout
        fig.update_layout(
            title={
                'text': "Object Persistence Analysis",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 20}
            },
            height=400,
            width=600,
            template="plotly_white",
            showlegend=True,
            font=dict(size=18)
        )

        return fig

    def _extract_hash(self, obj_ref: str) -> str:
        """Extract hash from object reference"""
        match = re.search(r"@([0-9a-f]+)", obj_ref)
        return match.group(1) if match else obj_ref

    def _get_object_size(self, obj_hash: str) -> int:
        """Helper to get object size from hash"""
        if obj_hash in self.memory_objects:
            return self.memory_objects[obj_hash].size
        return 0
