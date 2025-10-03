import streamlit as st
from typing import Dict
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from collections import defaultdict

from parsers.bytecode_parser import BytecodeParser
from visualizers.dependency_graph import DependencyGraphVisualizer
from visualizers.memory_timeline import MemoryTimelineVisualizer
from visualizers.object_flow import ObjectFlowVisualizer
from visualizers.bytecode_distribution import BytecodeDistributionVisualizer
from analyzers.performance_analyzer import PerformanceAnalyzer
from analyzers.memory_analyzer import MemoryAnalyzer
from analyzers.task_analyzer import TaskAnalyzer

# Set page configuration
st.set_page_config(
    page_title="TornadoVM Bytecode Visualizer",
    page_icon="🌪️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def find_in_parents(relative_path: str):
    """Walk up from this script's directory and return the first path that exists."""
    try:
        start = Path(__file__).resolve().parent
    except NameError:
        start = Path.cwd().resolve()

    for folder in [start, *start.parents]:
        candidate = folder / relative_path
        if candidate.exists():
            return candidate
    return None

def main():
    # Apply custom CSS for dark theme
    st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
        font-size: 16px;
    }
    h1 {
        color: #ffffff;
        font-size: 32px;
    }
    h2 {
        color: #ffffff;
        font-size: 26px;
    }
    h3 {
        color: #ffffff;
        font-size: 22px;
    }
    .stMarkdown {
        font-size: 16px;
    }
    .stDataFrame {
        font-size: 16px;
    }
    .stSelectbox {
        font-size: 16px;
    }
    .stRadio {
        font-size: 16px;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 5px;
        font-size: 16px;
    }
    .metric-card {
        background-color: #1e2130;
        border-radius: 5px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        font-size: 16px;
    }
    .dashboard-title {
        text-align: center;
        margin-bottom: 30px;
        font-size: 18px;
    }
    .task-summary {
        white-space: pre-wrap !important;
        font-family: monospace !important;
        font-size: 16px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # App header with logo
    st.markdown("""
    <div class="dashboard-title">
        <h1>🌪️ TornadoVM Bytecode Visualizer</h1>
        <p>Analyze and visualize TornadoVM bytecode execution patterns and memory operations</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar for navigation and file upload
    with st.sidebar:
        st.header("Upload Data")
        uploaded_file = st.file_uploader(
            "Upload TornadoVM bytecode log",
            type=["txt", "log"],
            key="tornado_log_uploader"
        )

        if uploaded_file:
            st.success(f"File uploaded: {uploaded_file.name}")
            page = st.radio(
                "Select View:",
                ["Basic Overview", "Task Graphs", "Memory Analysis", "Bytecode Details"],
                index=0,
                key="page_selector"
            )
        else:
            st.info("Please upload a TornadoVM bytecode log to begin")
            page = "Welcome"

    # Show welcome screen when no file is uploaded
    if not uploaded_file:
        st.header("Welcome to TornadoVM Bytecode Analyzer")

        st.markdown("""
        This tool helps you analyze TornadoVM bytecode execution logs to understand:

        - **Task Graph Structure**: Visualize how task graphs depend on each other
        - **Memory Operations**: Track allocations, transfers, and deallocations
        - **Data Dependencies**: See how objects flow between different task graphs
        - **Performance Insights**: Identify potential memory bottlenecks

        ### Getting Started

        1. Upload a TornadoVM bytecode log file using the sidebar
        2. Explore different visualizations using the navigation options
        3. Gain insights into your TornadoVM application's behavior

        ### Sample Visualization
        """)

        # Resolve and show example image from docs by walking parent folders
        img_path = find_in_parents("docs/images/basic_view.png")
        if img_path is not None:
            st.image(
                str(img_path),
                caption="Example task graph visualization",
                use_column_width=True
            )
        else:
            st.info("Sample image not found in any parent 'docs/images' folder.")
        return

    # Process uploaded file
    try:
        log_content = uploaded_file.read().decode("utf-8")
        parser = BytecodeParser()
        parser.parse_log(log_content)

        # Get graphs and memory objects
        graphs = parser.graphs
        memory_objects = parser.memory_objects
        bytecode_details = parser.bytecode_details

        # Basic metrics
        num_task_graphs = len(graphs)
        total_objects = len(memory_objects)
        total_bytecodes = len(bytecode_details)

        # Calculate total tasks by counting LAUNCH operations
        total_tasks = sum(1 for bc in bytecode_details
                         if bc.get("Operation") == "LAUNCH" and bc.get("TaskName"))
        # If no LAUNCH operations found, count task graph entries
        if total_tasks == 0:
            total_tasks = sum(len(graph.tasks) for graph in graphs.values())

        # Calculate memory metrics
        total_allocated = sum(obj.size for obj in memory_objects.values())

        # Create analyzers and visualizers
        performance_analyzer = PerformanceAnalyzer(graphs, memory_objects)
        memory_analyzer = MemoryAnalyzer(graphs, memory_objects)
        task_analyzer = TaskAnalyzer(graphs)

        dep_graph_viz = DependencyGraphVisualizer(graphs, memory_objects)
        memory_timeline_viz = MemoryTimelineVisualizer(graphs, memory_objects)
        object_flow_viz = ObjectFlowVisualizer(graphs, memory_objects)
        bytecode_dist_viz = BytecodeDistributionVisualizer(graphs)

        # Get summary dataframe with enhanced task details
        summary_df = performance_analyzer.generate_task_summary()

        # Different pages based on sidebar selection
        if page == "Basic Overview":
            st.header("Overview Dashboard")

            # Display key metrics in a row
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Task Graphs", num_task_graphs)
            with col2:
                st.metric("Total Tasks", total_tasks)
            with col3:
                st.metric("Total Objects", total_objects)
            with col4:
                st.metric("Memory (MB)", f"{total_allocated/(1024*1024):.2f}")
            with col5:
                st.metric("Total Bytecodes", total_bytecodes)

            # Display summary table
            st.subheader("Task Graph Summary")
            # Configure the dataframe display
            st.markdown("""
            <style>
            .task-summary {
                white-space: pre-wrap !important;
                font-family: monospace !important;
            }
            .stDataFrame {
                width: 100% !important;
            }
            .task-indent {
                padding-left: 20px;
            }
            </style>
            """, unsafe_allow_html=True)

            # Display with custom formatting
            st.dataframe(
                summary_df,
                column_config={
                    "Dependencies": st.column_config.TextColumn(
                        "Dependencies",
                        help="For task graphs: object dependencies between graphs. For tasks: operation counts.",
                        max_chars=1000,
                        width="large"
                    ),
                    "Task": st.column_config.TextColumn(
                        "Task",
                        help="Task graph summary and individual tasks",
                        width="large"
                    ),
                    "TaskGraph": st.column_config.TextColumn(
                        "TaskGraph",
                        help="Task graph identifier",
                        width="small"
                    ),
                    "Device": st.column_config.TextColumn(
                        "Device",
                        help="Execution device",
                        width="medium"
                    ),
                    "NumOperations": st.column_config.NumberColumn(
                        "Operations",
                        help="Number of operations in the task/graph",
                        format="%d"
                    ),
                    "TotalMemoryAllocated (MB)": st.column_config.NumberColumn(
                        "Memory Allocated (MB)",
                        help="Total memory allocated in MB",
                        format="%.2f"
                    ),
                    "TotalMemoryTransferred (MB)": st.column_config.NumberColumn(
                        "Memory Transferred (MB)",
                        help="Total memory transferred in MB",
                        format="%.2f"
                    ),
                    "Allocations": st.column_config.NumberColumn(
                        "Allocs",
                        help="Number of allocation operations",
                        format="%d"
                    ),
                    "Deallocations": st.column_config.NumberColumn(
                        "Deallocs",
                        help="Number of deallocation operations",
                        format="%d"
                    ),
                    "PersistedObjects": st.column_config.NumberColumn(
                        "Persisted",
                        help="Number of persisted objects",
                        format="%d"
                    )
                },
                hide_index=True,
                use_container_width=True
            )

            # Basic charts in two columns
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Memory Usage")
                mem_chart = memory_analyzer.get_memory_usage_chart()
                if mem_chart:
                    st.plotly_chart(mem_chart, use_container_width=True)

            with col2:
                st.subheader("Bytecode Distribution")
                bc_chart = bytecode_dist_viz.visualize()
                st.plotly_chart(bc_chart, use_container_width=True)

            # Add some space before the dependency graph
            st.write("")
            st.write("")

            # Simple dependency graph at the bottom
            st.markdown("##### Task Graph Dependencies")
            simple_graph = dep_graph_viz.visualize_simple()
            if simple_graph:
                # Add CSS to center the graph
                st.markdown("""
                <style>
                .simple-graph-container {
                    display: flex;
                    justify-content: center;
                    margin-top: -20px;
                }
                </style>
                """, unsafe_allow_html=True)
                st.markdown('<div class="simple-graph-container">', unsafe_allow_html=True)
                st.pyplot(simple_graph)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("No task graph dependencies to display")

        elif page == "Task Graphs":
            st.header("Task Graph Analysis")

            st.markdown("""
            Visualize and analyze task graph dependencies and their structure:

            **Left**: Task graph dependency visualization showing data flow between graphs.

            **Right**: Detailed view of selected task graph, including device info, tasks, and bytecode operations.
            """)

            # Split into two columns
            col1, col2 = st.columns([1, 1])

            with col1:
                # Detailed dependency visualization
                st.subheader("Task Graph Dependencies")
                dep_graph_viz.visualize_detailed_graphviz()

            with col2:
                # Task details
                st.subheader("Task Details")

                # Select a specific task graph
                if graphs:
                    selected_graph_id = st.selectbox(
                        "Select Task Graph:",
                        options=list(graphs.keys())
                    )

                    # Show selected graph details
                    selected = graphs.get(selected_graph_id)
                    if selected:
                        st.markdown(f"**Device:** {selected.device}")
                        st.markdown(f"**Operations:** {len(selected.operations)}")

                        # Show tasks
                        st.markdown("**Tasks:**")
                        for task in selected.tasks:
                            st.markdown(f"- {task}")

                        # Show dependencies with object details
                        st.markdown("""
                        <style>
                        .dep-source {
                            margin-top: 8px;
                            margin-bottom: 4px;
                            font-weight: bold;
                        }
                        .dep-type {
                            margin-left: 20px;
                            margin-top: 4px;
                            margin-bottom: 4px;
                            color: #E0E0E0;
                        }
                        .dep-hash {
                            margin-left: 40px;
                            font-family: monospace;
                            color: #9ECBFF;
                        }
                        </style>
                        """, unsafe_allow_html=True)

                        st.markdown("**Dependencies:**")
                        if selected.dependencies:
                            # Group dependencies by source graph
                            grouped_deps = defaultdict(list)
                            for dep_graph, objs in selected.dependencies.items():
                                for obj_hash in objs:
                                    obj_type = dep_graph_viz._find_object_type(obj_hash, selected, dep_graph)
                                    grouped_deps[dep_graph].append((obj_type, obj_hash[:6]))

                            # Display dependencies
                            for dep_graph, obj_list in grouped_deps.items():
                                st.markdown(f'<div class="dep-source">• From {dep_graph}</div>', unsafe_allow_html=True)
                                by_type = defaultdict(list)
                                for obj_type, hash_id in obj_list:
                                    by_type[obj_type].append(hash_id)

                                for i, (obj_type, hashes) in enumerate(sorted(by_type.items()), 1):
                                    st.markdown(f'<div class="dep-type">{i}. {obj_type}</div>', unsafe_allow_html=True)
                                    for hash_id in sorted(hashes):
                                        st.markdown(f'<div class="dep-hash">@{hash_id}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="dep-type">No dependencies</div>', unsafe_allow_html=True)

                        # Show bytecodes
                        st.subheader("Bytecode Operations")
                        bytecode_df = pd.DataFrame([
                            {"Operation": op.operation,
                             "Objects": ", ".join(op.objects),
                             "Task": op.task_name,
                             "Size": op.size if hasattr(op, "size") and op.size else 0,
                             "Status": op.status if hasattr(op, "status") and op.status else ""}
                            for op in selected.operations
                        ])
                        st.dataframe(bytecode_df)
                else:
                    st.info("No task graphs found in the log file")

        elif page == "Memory Analysis":
            st.header("Memory Analysis")

            # Memory timeline
            st.subheader("Memory Objects Lifecycle")

            # Simplify to a basic chart if the interactive one fails
            try:
                timeline_fig = memory_timeline_viz.visualize()
                st.plotly_chart(timeline_fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error generating memory timeline: {e}")
                st.info("Showing simplified memory usage chart instead")
                mem_chart = memory_analyzer.get_memory_usage_chart()
                if mem_chart:
                    st.plotly_chart(mem_chart, use_container_width=True)

            # Object details
            st.subheader("Object Analysis")

            col1, col2 = st.columns([1, 2])

            with col1:
                # Object selection dropdown
                object_options = []
                for obj_id, obj in memory_objects.items():
                    short_type = obj.object_type.split('.')[-1]
                    object_options.append((f"{short_type}@{obj_id[:8]}", obj_id))

                if object_options:
                    selected_object = st.selectbox(
                        "Select Object:",
                        options=[obj_id for _, obj_id in object_options],
                        format_func=lambda x: next((name for name, id in object_options if id == x), x)
                    )

                    # Show object details
                    if selected_object in memory_objects:
                        obj = memory_objects[selected_object]
                        st.markdown(f"**Type:** {obj.object_type}")
                        st.markdown(f"**Size:** {obj.size:,} bytes ({obj.size/1024/1024:.2f} MB)")
                        st.markdown(f"**Status:** {obj.current_status}")
                        st.markdown(f"**Allocated in:** {obj.allocated_in_graph}")
                else:
                    st.info("No objects found in the log file")
                    selected_object = None

            with col2:
                # Object flow visualization
                if object_options and selected_object:
                    try:
                        flow_fig = object_flow_viz.visualize(selected_object)
                        st.plotly_chart(flow_fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error generating object flow: {e}")

            # Memory statistics charts
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Memory Usage Over Time")
                mem_chart = memory_analyzer.get_memory_usage_chart()
                if mem_chart:
                    st.plotly_chart(mem_chart, use_container_width=True)

            with col2:
                st.subheader("Object Persistence")
                persistence_chart = memory_analyzer.get_object_persistence_chart()
                if persistence_chart:
                    st.plotly_chart(persistence_chart, use_container_width=True)

        elif page == "Bytecode Details":
            st.header("Bytecode Analysis")

            # Use full width container
            st.markdown("""
            <style>
            .block-container {
                padding-top: 1rem;
                padding-bottom: 0rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }
            .stDataFrame {
                width: 100% !important;
            }
            .dataframe-container {
                margin-top: 1rem;
                margin-bottom: 2rem;
            }
            </style>
            """, unsafe_allow_html=True)

            # Operations by Task Graph - make it wider and more readable
            st.subheader("Operations by Task Graph")

            # Create pivot table for operations
            if bytecode_details:
                bc_by_graph = defaultdict(lambda: defaultdict(int))
                for bc in bytecode_details:
                    bc_by_graph[bc.get("TaskGraph")][bc.get("Operation")] += 1

                # Create heatmap data
                graph_ops = []
                for graph, ops in bc_by_graph.items():
                    for op, count in ops.items():
                        graph_ops.append({"TaskGraph": graph, "Operation": op, "Count": count})

                graph_ops_df = pd.DataFrame(graph_ops)

                if not graph_ops_df.empty:
                    # Create a pivot table with better formatting
                    pivot_df = graph_ops_df.pivot_table(
                        index="TaskGraph",
                        columns="Operation",
                        values="Count",
                        aggfunc='sum',
                        fill_value=0
                    )

                    # Reorder columns in a logical sequence
                    preferred_order = [
                        "ALLOC", "ON_DEVICE", "ON_DEVICE_BUFFER",
                        "TRANSFER_HOST_TO_DEVICE", "TRANSFER_HOST_TO_DEVICE_ONCE", "TRANSFER_HOST_TO_DEVICE_ALWAYS",
                        "TRANSFER_DEVICE_TO_HOST", "TRANSFER_DEVICE_TO_HOST_ALWAYS",
                        "LAUNCH", "BARRIER", "DEALLOC"
                    ]

                    # Reorder columns while keeping any additional columns at the end
                    ordered_cols = [col for col in preferred_order if col in pivot_df.columns]
                    remaining_cols = [col for col in pivot_df.columns if col not in preferred_order]
                    pivot_df = pivot_df[ordered_cols + remaining_cols]

                    # Display the pivot table with custom formatting
                    st.dataframe(
                        pivot_df,
                        column_config={
                            col: st.column_config.NumberColumn(
                                col,
                                help=f"Number of {col} operations",
                                format="%d"
                            ) for col in pivot_df.columns
                        },
                        use_container_width=True
                    )

            # Bytecode listing with filters
            st.subheader("Bytecode Listing")

            if bytecode_details:
                # Filters in a single row
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    graph_filter = st.multiselect(
                        "Filter by Task Graph",
                        options=sorted(set(bc.get("TaskGraph") for bc in bytecode_details))
                    )
                with col2:
                    op_filter = st.multiselect(
                        "Filter by Operation",
                        options=sorted(set(bc.get("Operation") for bc in bytecode_details))
                    )
                with col3:
                    search_term = st.text_input("Search Objects")

                # Apply filters
                filtered_bc = bytecode_details
                if graph_filter:
                    filtered_bc = [bc for bc in filtered_bc if bc.get("TaskGraph") in graph_filter]
                if op_filter:
                    filtered_bc = [bc for bc in filtered_bc if bc.get("Operation") in op_filter]
                if search_term:
                    filtered_bc = [bc for bc in filtered_bc if search_term.lower() in bc.get("Objects", "").lower()]

                # Create DataFrame with desired column order
                bc_df = pd.DataFrame(filtered_bc)
                if not bc_df.empty:
                    # Reorder columns
                    bc_df = bc_df[['TaskGraph', 'Operation', 'TaskName', 'Objects', 'GlobalIndex', 'Details']]

                    # Display filtered data with improved formatting
                    st.dataframe(
                        bc_df,
                        column_config={
                            "TaskGraph": st.column_config.TextColumn(
                                "TaskGraph",
                                help="Task graph identifier",
                                width="medium"
                            ),
                            "Operation": st.column_config.TextColumn(
                                "Operation",
                                help="Bytecode operation type",
                                width="medium"
                            ),
                            "TaskName": st.column_config.TextColumn(
                                "TaskName",
                                help="Name of the task",
                                width="medium"
                            ),
                            "Objects": st.column_config.TextColumn(
                                "Objects",
                                help="Objects involved in the operation",
                                width="large"
                            ),
                            "GlobalIndex": st.column_config.NumberColumn(
                                "Index",
                                help="Global operation index",
                                format="%d"
                            ),
                            "Details": st.column_config.TextColumn(
                                "Details",
                                help="Operation details",
                                width="large"
                            )
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    st.info("No bytecodes match the selected filters")
            else:
                st.info("No bytecode details found in the log file")

    except Exception as e:
        st.error(f"Error processing log file: {str(e)}")
        st.info("Please check that the file contains valid TornadoVM bytecode logs")

if __name__ == "__main__":
    main()
