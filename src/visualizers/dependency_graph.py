import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import graphviz
import streamlit as st
from typing import Optional, Dict, List
from collections import defaultdict
from models.task_graph import TaskGraph

class DependencyGraphVisualizer:
    """Visualizes task graph dependencies"""

    def __init__(self, graphs: Dict[str, TaskGraph], memory_objects: Dict = None):
        self.graphs = graphs
        self.memory_objects = memory_objects or {}
        
    def visualize_detailed_graphviz(self) -> None:
        """Visualize task dependencies using Graphviz for detailed view"""
        try:
            # Create a new Graphviz graph
            dot = graphviz.Digraph(
                comment='Task Dependencies',
                format='svg',
                engine='dot'
            )

            # Set graph attributes for more compact visualization
            dot.attr(
                rankdir='TB',  # Top to bottom layout
                splines='ortho',  # Orthogonal lines
                nodesep='0.35',  # Node separation
                ranksep='0.4',  # Rank separation
                size='5,4',  # Size
                ratio='compress',  # Compress to fit
                bgcolor='transparent'
            )

            # Set default node attributes
            dot.attr('node',
                    shape='box',
                    style='filled',
                    fillcolor='#1e1e1e',
                    color='#666666',
                    fontcolor='white',
                    fontname='Arial',
                    fontsize='12',
                    margin='0.15',
                    height='0.4',
                    width='1.8')

            # Set default edge attributes
            dot.attr('edge',
                    color='#666666',
                    fontcolor='white',
                    fontname='Arial',
                    fontsize='11',
                    penwidth='0.7')

            # Add nodes for each task graph
            for graph_id, graph in self.graphs.items():
                # Create node label
                op_counts = defaultdict(int)
                for op in graph.operations:
                    op_counts[op.operation] += 1

                # Format the label
                label = f"{graph_id}\\n{sum(op_counts.values())} ops"

                # Add node
                dot.node(graph_id, label)

            # Add edges for dependencies
            for graph_id, graph in self.graphs.items():
                for dep_graph_id, objects in graph.dependencies.items():
                    if objects:
                        # Get object names and types
                        obj_details = []
                        for obj_hash in objects:
                            obj_type = self._find_object_type(obj_hash, graph, dep_graph_id)
                            obj_details.append(f"{obj_type}@{obj_hash[:6]}")

                        # Add edge with all object names
                        edge_label = '\\n'.join(sorted(obj_details))
                        dot.edge(dep_graph_id, graph_id, edge_label)

            # Add custom CSS for container
            st.markdown("""
            <style>
            .graph-container {
                background: #0e1117;
                border-radius: 10px;
                padding: 12px;
                margin: 8px 0;
            }
            .graph-container svg {
                width: 100%;
                height: auto;
                min-height: 350px;
                max-height: 600px;
            }
            </style>
            """, unsafe_allow_html=True)

            # Create container with column layout
            st.markdown('<div class="graph-container">', unsafe_allow_html=True)
            col1 = st.columns([3])[0]
            with col1:
                st.graphviz_chart(dot)
            st.markdown('</div>', unsafe_allow_html=True)

            # Add summary metrics
            col1, col2, col3 = st.columns([1,1,1])
            with col1:
                st.metric('Graphs', len(self.graphs))
            with col2:
                st.metric('Deps', sum(len(g.dependencies) for g in self.graphs.values()))
            with col3:
                st.metric('Ops', sum(len(g.operations) for g in self.graphs.values()))

        except Exception as e:
            st.error(f"Error generating dependency graph: {e}")
            st.info("Please check that the task graphs contain valid data")

    def _find_object_type(self, obj_hash: str, graph: TaskGraph, dep_graph_id: str) -> str:
        """Helper method to find object type from various sources"""
        # Try memory objects first
        if obj_hash in self.memory_objects:
            obj = self.memory_objects[obj_hash]
            return self._extract_type(obj.object_type)

        # Try current graph operations
        for op in graph.operations:
            for obj_ref in op.objects:
                if self._extract_hash(obj_ref) == obj_hash:
                    return self._extract_type(obj_ref)

        # Try source graph operations
        source_graph = self.graphs.get(dep_graph_id)
        if source_graph:
            for op in source_graph.operations:
                for obj_ref in op.objects:
                    if self._extract_hash(obj_ref) == obj_hash:
                        return self._extract_type(obj_ref)

        return "Unknown"

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

        # Handle empty graph
        if len(G.nodes()) == 0:
            fig = go.Figure()
            fig.add_annotation(
                text="No task graphs available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20)
            )
            fig.update_layout(title='Task Graph Dependencies')
            return fig

        # Create interactive visualization
        pos = nx.spring_layout(G)

        # Create edges
        edge_trace = go.Scatter(
            x=[], y=[],
            line=dict(width=0.5, color='#888'),
            hoverinfo='text',
            mode='lines',
            text=[])

        # Create nodes
        node_trace = go.Scatter(
            x=[], y=[],
            mode='markers+text',
            hoverinfo='text',
            marker=dict(
                showscale=False,
                color='lightblue',
                size=20,
                line=dict(width=2, color='darkblue')
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

        # Add nodes to the trace
        node_labels = []
        hover_texts = []
        for node in G.nodes():
            x, y = pos[node]
            node_trace['x'] += tuple([x])
            node_trace['y'] += tuple([y])
            tasks_str = ', '.join(G.nodes[node]['tasks']) if G.nodes[node]['tasks'] else 'No tasks'
            node_labels.append(node)
            hover_texts.append(f"Graph: {node}<br>Device: {G.nodes[node]['device']}<br>Thread: {G.nodes[node]['thread']}<br>Tasks: {tasks_str}")

        node_trace['text'] = node_labels
        node_trace['hovertext'] = hover_texts

        # Create the figure
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title='Task Graph Dependencies',
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                       ))

        return fig
        
    def visualize_simple(self) -> Optional[plt.Figure]:
        """Creates a simpler dependency graph visualization"""
        if not self.graphs:
            return None

        # Create a new graph with init and end nodes
        viz_graph = nx.DiGraph()

        # Add all nodes from graphs
        for node in self.graphs.keys():
            viz_graph.add_node(node)

        # Add edges based on dependencies
        for graph_id, graph in self.graphs.items():
            for dep_graph_id in graph.dependencies.keys():
                if dep_graph_id in self.graphs:
                    viz_graph.add_edge(dep_graph_id, graph_id)

        # Find start and end nodes
        start_nodes = [n for n in viz_graph.nodes() if viz_graph.in_degree(n) == 0]
        end_nodes = [n for n in viz_graph.nodes() if viz_graph.out_degree(n) == 0]

        # Add Init and End nodes
        if start_nodes:
            viz_graph.add_node("Init")
            for node in start_nodes:
                viz_graph.add_edge("Init", node)

        if end_nodes:
            viz_graph.add_node("End")
            for node in end_nodes:
                viz_graph.add_edge(node, "End")

        # Set style for better visualization
        plt.style.use('dark_background')
        # Adjust figure size based on number of nodes
        num_nodes = len(viz_graph.nodes())
        width = max(5, min(8, 5 + (num_nodes - 5) * 0.5))  # Scale width with nodes
        height = max(4, min(6, 4 + (num_nodes - 5) * 0.3))  # Scale height with nodes
        fig, ax = plt.subplots(figsize=(width, height))
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#0e1117')

        try:
            # Use different layout algorithms based on graph size and structure
            if num_nodes <= 5:
                pos = nx.spring_layout(viz_graph, k=2.0, iterations=50, seed=42)
            else:
                # Try kamada_kawai_layout for better node distribution
                try:
                    pos = nx.kamada_kawai_layout(viz_graph, scale=2.0)
                except:
                    # Fallback to spring layout with more iterations and stronger repulsion
                    pos = nx.spring_layout(viz_graph, k=2.0, iterations=50, seed=42)

            # Scale positions to prevent nodes from going outside the plot
            pos = {node: (x * 0.8, y * 0.8) for node, (x, y) in pos.items()}

            # Draw regular nodes
            regular_nodes = [n for n in viz_graph.nodes() if n not in ["Init", "End"]]
            nx.draw_networkx_nodes(viz_graph, pos,
                                  nodelist=regular_nodes,
                                  node_size=900,  # Slightly smaller nodes
                                  node_color='#648FFF',  # IBM colorblind-safe blue
                                  alpha=0.9,
                                  edgecolors='white',
                                  linewidths=0.5,
                                  ax=ax)

            # Draw Init and End nodes with different style
            init_end_nodes = [n for n in viz_graph.nodes() if n in ["Init", "End"]]
            if init_end_nodes:
                nx.draw_networkx_nodes(viz_graph, pos,
                                      nodelist=init_end_nodes,
                                      node_size=700,  # Slightly smaller special nodes
                                      node_color='#DC267F',  # IBM colorblind-safe magenta
                                      alpha=0.9,
                                      edgecolors='white',
                                      linewidths=0.5,
                                      ax=ax)

            # Draw edges with bolder styling
            nx.draw_networkx_edges(viz_graph, pos,
                                  width=1.2,
                                  edge_color='#785EF0',  # IBM colorblind-safe purple
                                  alpha=0.8,
                                  arrowsize=15,
                                  arrowstyle='-|>',
                                  connectionstyle='arc3,rad=0.2',  # More curved edges
                                  min_target_margin=25,  # Increased margin
                                  min_source_margin=25,  # Increased margin
                                  ax=ax)

            # Add labels with larger font
            nx.draw_networkx_labels(viz_graph, pos,
                                   font_size=8,  # Increased from 6
                                   font_family='monospace',
                                   font_weight='bold',
                                   font_color='white',
                                   bbox=dict(facecolor='#0e1117',
                                           edgecolor='none',
                                           alpha=0.7,
                                           pad=0.2),
                                   ax=ax)

            plt.title("")
            plt.axis("off")

            # Add more padding around the plot
            plt.tight_layout(pad=0.8)  # More padding
            # Increase margins for better spacing
            ax.margins(x=0.25, y=0.25)

            return fig
        except Exception as e:
            st.error(f"Error generating simple dependency graph: {e}")
            return None
