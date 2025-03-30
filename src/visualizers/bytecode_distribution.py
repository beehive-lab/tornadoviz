import plotly.express as px
import pandas as pd
from typing import Dict
from ..models.task_graph import TaskGraph

class BytecodeDistributionVisualizer:
    """Visualizes bytecode operation distribution"""
    
    def __init__(self, graphs: Dict[str, TaskGraph]):
        self.graphs = graphs
        
    def visualize(self) -> px.Figure:
        """Create an interactive bytecode operation distribution visualization"""
        # Collect operation data
        operation_data = []
        
        for graph_id, graph in self.graphs.items():
            for op in graph.operations:
                operation_data.append({
                    'Graph': graph_id,
                    'Operation': op.operation,
                    'Task': op.task_name,
                    'Device': graph.device,
                    'Thread': graph.thread
                })
                
        # Create DataFrame
        df = pd.DataFrame(operation_data)
        
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
