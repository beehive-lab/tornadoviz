# TornadoViz <img src="docs/images/img.png" width="32" height="32" alt="Icon" align="left" style="margin-right: 10px;">

A visualization and analysis tool for TornadoVM bytecode execution logs that helps developers understand and optimize their applications running on [TornadoVM](https://github.com/beehive-lab/TornadoVM).

## Overview

The TornadoVM Bytecode Analyzer provides interactive visualizations and detailed analysis of task graphs, memory operations, and bytecode execution patterns. This helps developers optimize their applications and understand data flow between tasks.

<p align="center">
  <img src="docs/images/demo.gif" width="800" alt="TornadoVM Bytecode Analyzer Demo" style="display: block; margin: 20px auto;">
</p>

The analyzer offers multiple views for comprehensive analysis of your TornadoVM applications:

<img src="docs/images/basic_view.png" width="800" alt="TornadoVM Bytecode Analyzer Basic View" style="display: block; margin: 20px auto;">

## Features

### Task Graph Analysis
- Visualize task graph dependencies and execution flow
- Analyze memory operations and data transfers between tasks
- Track object lifecycles across different task graphs
- Identify memory allocation patterns and potential bottlenecks

### Memory Analysis
The tool provides detailed memory operation analysis:

<img src="docs/images/memory_analysis.png" width="800" alt="TornadoVM Memory Analysis View" style="display: block; margin: 20px auto;">

- **Memory Timeline**: Track memory operations across task graphs with:
  - 🟢 Memory allocations
  - 🔵 Host-to-device transfers
  - 🟣 Device-to-host transfers
  - 🔴 Memory deallocations
  - 🟠 Device buffer operations

- **Object Lifecycle**: Follow individual objects through their complete lifecycle
- **Memory Usage**: Monitor total memory usage and allocation patterns
- **Object Persistence**: Analyze object retention and deallocation patterns

### Bytecode Details
- Detailed view of all bytecode operations
- Filter and search capabilities
- Operation distribution analysis
- Task-specific operation breakdowns

## Task Graph Analysis

The Task Graph Analysis view provides insights into the execution flow and memory operations of your TornadoVM application:

- **Task Graph Dependencies**: Visualize how different task graphs depend on each other and the data flow between them
- **Memory Timeline**: Track memory allocations, deallocations, and overall memory usage across task graphs
- **Task Details**: Examine individual tasks, their operations, and memory patterns

<p align="center">
  <img src="docs/images/task_graph_analysis.png" width="800" alt="Task Graph Analysis View">
</p>

The visualization shows:
- Vertical lines separating different task graphs
- Memory usage over time (blue line)
- Allocations (green dots) and deallocations (red X)
- Task boundaries and execution sequence

## Installation

### Prerequisites
- Python 3.8 or higher

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the analyzer:
```bash
streamlit run tornado-visualizer-fixed.py
```

## Contributing

This tool is part of the TornadoVM project. For contributions, please follow the [TornadoVM contribution guidelines](https://github.com/beehive-lab/TornadoVM/blob/master/CONTRIBUTING.md).

## Acknowledgments

This work is partially funded by the following EU & UKRI grants (most recent first):

- EU Horizon Europe & UKRI [AERO 101092850](https://aero-project.eu/).
- EU Horizon Europe & UKRI [P2CODE 101093069](https://p2code-project.eu/).
- EU Horizon Europe & UKRI [ENCRYPT 101070670](https://encrypt-project.eu).
- EU Horizon Europe & UKRI [TANGO 101070052](https://tango-project.eu).
