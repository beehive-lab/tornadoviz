import streamlit as st
from typing import Dict
import pandas as pd
import plotly.graph_objects as go

from .parsers.bytecode_parser import BytecodeParser
from .visualizers.dependency_graph import DependencyGraphVisualizer
from .visualizers.memory_timeline import MemoryTimelineVisualizer
from .visualizers.object_flow import ObjectFlowVisualizer
from .visualizers.bytecode_distribution import BytecodeDistributionVisualizer
from .analyzers.performance_analyzer import PerformanceAnalyzer
from .analyzers.memory_analyzer import MemoryAnalyzer
from .analyzers.task_analyzer import TaskAnalyzer
from .utils.formatting import format_bytes, format_object_ref, format_task_name, format_device_name

# Set page configuration
st.set_page_config(
    page_title="TornadoVM Bytecode Visualizer",
    page_icon="🌪️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'parser' not in st.session_state:
    st.session_state.parser = BytecodeParser()
if 'graphs' not in st.session_state:
    st.session_state.graphs = {}
if 'memory_objects' not in st.session_state:
    st.session_state.memory_objects = {}

def main():
    st.title("TornadoVM Bytecode Visualizer")
    
    # File upload
    uploaded_file = st.file_uploader("Upload bytecode log file", type=['txt'])
    
    if uploaded_file is not None:
        # Parse the log file
        log_content = uploaded_file.getvalue().decode()
        st.session_state.parser.parse_log(log_content)
        st.session_state.graphs = st.session_state.parser.graphs
        st.session_state.memory_objects = st.session_state.parser.memory_objects
        
        # Create analyzers
        performance_analyzer = PerformanceAnalyzer(st.session_state.graphs)
        memory_analyzer = MemoryAnalyzer(st.session_state.graphs, st.session_state.memory_objects)
        task_analyzer = TaskAnalyzer(st.session_state.graphs)
        
        # Create visualizers
        dep_graph_viz = DependencyGraphVisualizer(st.session_state.graphs)
        memory_timeline_viz = MemoryTimelineVisualizer(st.session_state.graphs, st.session_state.memory_objects)
        object_flow_viz = ObjectFlowVisualizer(st.session_state.graphs, st.session_state.memory_objects)
        bytecode_dist_viz = BytecodeDistributionVisualizer(st.session_state.graphs)
        
        # Sidebar navigation
        st.sidebar.title("Navigation")
        page = st.sidebar.radio(
            "Select View",
            ["Overview", "Dependencies", "Memory", "Performance", "Tasks"]
        )
        
        if page == "Overview":
            show_overview(bytecode_dist_viz, performance_analyzer)
        elif page == "Dependencies":
            show_dependencies(dep_graph_viz)
        elif page == "Memory":
            show_memory(memory_timeline_viz, object_flow_viz, memory_analyzer)
        elif page == "Performance":
            show_performance(performance_analyzer)
        elif page == "Tasks":
            show_tasks(task_analyzer)

def show_overview(bytecode_dist_viz, performance_analyzer):
    st.header("Overview")
    
    # Bytecode distribution
    st.subheader("Bytecode Operation Distribution")
    st.plotly_chart(bytecode_dist_viz.visualize(), use_container_width=True)
    
    # Task summary
    st.subheader("Task Summary")
    task_summary = performance_analyzer.get_task_summary()
    st.dataframe(task_summary)

def show_dependencies(dep_graph_viz):
    st.header("Task Dependencies")
    
    # Detailed dependency graph
    st.subheader("Detailed Dependency Graph")
    st.plotly_chart(dep_graph_viz.visualize_detailed(), use_container_width=True)
    
    # Simple dependency graph
    st.subheader("Simple Dependency Graph")
    fig = dep_graph_viz.visualize_simple()
    if fig:
        st.pyplot(fig)

def show_memory(memory_timeline_viz, object_flow_viz, memory_analyzer):
    st.header("Memory Analysis")
    
    # Memory timeline
    st.subheader("Memory Timeline")
    st.plotly_chart(memory_timeline_viz.visualize(), use_container_width=True)
    
    # Object flow
    st.subheader("Object Flow")
    selected_object = st.selectbox(
        "Select Object",
        ["All"] + list(st.session_state.memory_objects.keys())
    )
    if selected_object == "All":
        selected_object = None
    st.plotly_chart(object_flow_viz.visualize(selected_object), use_container_width=True)
    
    # Memory usage statistics
    st.subheader("Memory Usage Statistics")
    memory_usage = memory_analyzer.get_memory_usage()
    st.dataframe(memory_usage)

def show_performance(performance_analyzer):
    st.header("Performance Analysis")
    
    # Task summary
    st.subheader("Task Summary")
    task_summary = performance_analyzer.get_task_summary()
    st.dataframe(task_summary)
    
    # Operation timing
    st.subheader("Operation Timing")
    timing_data = performance_analyzer.get_operation_timing()
    st.dataframe(timing_data)
    
    # Device utilization
    st.subheader("Device Utilization")
    device_util = performance_analyzer.get_device_utilization()
    st.dataframe(device_util)

def show_tasks(task_analyzer):
    st.header("Task Analysis")
    
    # Task dependencies
    st.subheader("Task Dependencies")
    task_deps = task_analyzer.get_task_dependencies()
    st.dataframe(task_deps)
    
    # Task sequence
    st.subheader("Task Sequence")
    task_seq = task_analyzer.get_task_sequence()
    st.dataframe(task_seq)
    
    # Operation distribution
    st.subheader("Operation Distribution")
    op_dist = task_analyzer.get_task_operation_distribution()
    st.dataframe(op_dist)

if __name__ == "__main__":
    main()
