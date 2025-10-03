import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict
from models.task_graph import TaskGraph

class BytecodeDistributionVisualizer:
    """Visualizes bytecode operation distribution"""

    def __init__(self, graphs: Dict[str, TaskGraph]):
        self.graphs = graphs

    def visualize(self) -> go.Figure:
        """Create an interactive bytecode operation distribution visualization"""
        # Collect operation data
        operation_data = []

        for graph_id, graph in self.graphs.items():
            for op in graph.operations:
                operation_data.append({
                    'Graph': graph_id,
                    'Operation': op.operation,
                    'Task': op.task_name if op.task_name else 'N/A',
                    'Device': graph.device,
                    'Thread': graph.thread
                })

        # Create DataFrame
        df = pd.DataFrame(operation_data)

        # Handle empty data case
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available to visualize",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20)
            )
            fig.update_layout(
                title='Bytecode Operation Distribution',
                height=800
            )
            return fig

        # Create treemap visualization
        fig = px.treemap(df,
                        path=['Graph', 'Operation', 'Task'],
                        title='Bytecode Operation Distribution',
                        color='Operation',
                        color_discrete_sequence=px.colors.qualitative.Set3)

        # Update layout
        fig.update_layout(
            margin=dict(t=50, l=25, r=25, b=25),
            height=800
        )

        return fig
