import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from typing import Optional, Dict, List
from ..models.task_graph import TaskGraph

class DependencyGraphVisualizer:
    """Visualizes task graph dependencies"""
    
    def __init__(self, graphs: Dict[str, TaskGraph]):
        self.graphs = graphs
        
    def visualize_detailed(self) -> go.Figure:
        """Create a detailed interactive dependency graph visualization"""
        G = nx.DiGraph()
        
        # Add nodes for each graph
        for graph_id, graph in self.graphs.items():
            G.add_node(graph_id, 
                      device=graph.device,
                      thread=graph.thread,
                      tasks=graph.tasks)
                      
        # Add edges based on dependencies
        for graph_id, graph in self.graphs.items():
            for dep_graph_id, objects in graph.dependencies.items():
                if dep_graph_id in self.graphs:
                    G.add_edge(dep_graph_id, graph_id, objects=objects)
                    
        # Create interactive visualization
        pos = nx.spring_layout(G)
        
        # Create edges
        edge_trace = go.Scatter(
            x=[], y=[],
            line=dict(width=0.5, color='#888'),
            hoverinfo='text',
            mode='lines')
            
        # Create nodes
        node_trace = go.Scatter(
            x=[], y=[],
            mode='markers+text',
            hoverinfo='text',
            marker=dict(
                showscale=True,
                colorscale='YlOrRd',
                size=10,
                colorbar=dict(
                    thickness=15,
                    title='Node Connections',
                    xanchor='left',
                    titleside='right'
                )
            ),
            text=[],
            textposition="top center",
        )
        
        # Add edges to the trace
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace['x'] += tuple([x0, x1, None])
            edge_trace['y'] += tuple([y0, y1, None])
            edge_trace['text'] += tuple([f"Objects: {', '.join(G.edges[edge]['objects'])}"])
            
        # Add nodes to the trace
        for node in G.nodes():
            x, y = pos[node]
            node_trace['x'] += tuple([x])
            node_trace['y'] += tuple([y])
            node_trace['text'] += tuple([f"Graph: {node}<br>Device: {G.nodes[node]['device']}<br>Thread: {G.nodes[node]['thread']}<br>Tasks: {', '.join(G.nodes[node]['tasks'])}"])
            
        # Create the figure
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title='Task Graph Dependencies',
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40)
                       ))
                       
        return fig
        
    def visualize_simple(self) -> Optional[plt.Figure]:
        """Create a simple static dependency graph visualization"""
        G = nx.DiGraph()
        
        # Add nodes for each graph
        for graph_id, graph in self.graphs.items():
            G.add_node(graph_id, 
                      device=graph.device,
                      thread=graph.thread)
                      
        # Add edges based on dependencies
        for graph_id, graph in self.graphs.items():
            for dep_graph_id, objects in graph.dependencies.items():
                if dep_graph_id in self.graphs:
                    G.add_edge(dep_graph_id, graph_id)
                    
        # Create the visualization
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G)
        
        # Draw the graph
        nx.draw(G, pos, with_labels=True, node_color='lightblue', 
                node_size=1500, font_size=8, font_weight='bold',
                arrows=True, edge_color='gray')
                
        plt.title("Task Graph Dependencies")
        return plt.gcf()
