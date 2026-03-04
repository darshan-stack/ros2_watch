robowatch Architecture
======================

This document maps the robowatch implementation to the technical blueprint and ROS 2 concepts.

The blueprint describes six core components:

- Core robowatch CLI
- ROS2 Interaction Layer
- Data Collection Modules
- Analysis Engine
- Reporting and Recommendation Module
- Data Storage (ephemeral, MCAP)

The current implementation focuses on a Python-first version aligned with ROS 2 best practices as documented in the official ROS 2 docs (`https://github.com/ros2/ros2_documentation`, `https://docs.ros.org/en`).

### Core robowatch CLI

- **Role**: Command parsing, argument validation, feature orchestration.
- **Implementation**: `robowatch/cli.py`, `robowatch/__main__.py`.
- **Details**:
  - Uses `typer` to expose commands: `pulse`, `watch`, `trace`, `diff`, `doctor`.
  - Each command delegates to a dedicated module (feature dispatcher pattern).

### ROS2 Interaction Layer

- **Role**: Abstracts `rclpy` APIs and prepares for future `rclcpp`/DDS/tracing integration.
- **Implementation**:
  - `pulse.py`: `GraphIntrospectionNode` for node/topic graph queries.
  - `watch.py`: `WatchIntrospectionNode` for QoS and node-level introspection.
  - `trace_cmd.py`: `TraceNode` for topic subscriptions and timestamp capture.
  - `doctor.py`: `DoctorNode` for graph-level checks.
- **ROS 2 alignment**:
  - Follows node and graph concepts from the ROS 2 docs (nodes, topics, QoS profiles, discovery).
  - Uses `rclpy` spinning and graph APIs consistent with examples in the ROS 2 documentation.

### Data Collection Modules

- **Role**: Gather specific diagnostic data via the interaction layer.
- **Implementation**:
  - `pulse.py`:
    - Node and topic discovery via `get_node_names_and_namespaces` and `get_topic_names_and_types`.
    - CPU and RAM via `psutil` (system resource monitor).
  - `watch.py`:
    - QoS monitoring using publisher/subscription endpoint info and `qos_profile`.
    - Node-local CPU and memory usage via `psutil`.
  - `trace_cmd.py`:
    - Message flow timestamps per topic using subscriptions.
  - `diff_cmd.py`:
    - Topic frequencies and durations from MCAP files.
  - `doctor.py`:
    - Graph-level anomalies (publishers without subscribers, subscribers without publishers).

These correspond to the blueprint's Node and Topic Discovery, QoS Monitor, Message Flow Monitor, Timestamp Collector, and System Resource Monitor.

### Analysis Engine

- **Role**: Transform raw data into higher-level diagnostics (latencies, mismatches, regressions, health evaluation).
- **Implementation**:
  - `pulse.py`:
    - Classifies topics (`alive`, `no_subscribers`, `no_publishers`, `idle`).
    - Classifies nodes (`active`, `zombie_candidate`).
  - `watch.py`:
    - Compares QoS policies and synthesizes human-readable mismatch explanations.
  - `trace_cmd.py`:
    - Estimates hop-by-hop and total pipeline latency from per-topic timestamps.
  - `diff_cmd.py`:
    - Computes per-topic frequencies and highlights significant changes between runs.
  - `doctor.py`:
    - Aggregates graph checks into a list of issues with severities and recommendations.

These modules implement the blueprint's Pipeline Latency Calculator, QoS Mismatch Detector, Bottleneck Identifier (early form), Regression Analyzer, and Health Rule Engine (initial rules).

### Reporting and Recommendation Module

- **Role**: Present analysis results in clear, actionable terminal output.
- **Implementation**:
  - All feature modules (`pulse.py`, `watch.py`, `trace_cmd.py`, `diff_cmd.py`, `doctor.py`) use `rich` to format tables and plain text summaries.
  - `doctor.py` includes explicit recommendations for each detected issue, aligned with common ROS 2 troubleshooting patterns.

As the knowledge base grows, the recommendation logic can be centralized into a dedicated helper module that encodes more complex rules and links to relevant sections from the ROS 2 documentation.

### Data Storage (Ephemeral / MCAP)

- **Role**: Provide recorded data for regression and offline comparison.
- **Implementation**:
  - `diff_cmd.py` uses `mcap.reader.make_reader` to parse MCAP files and derive metrics.
  - Storage is treated as an external input; robowatch does not perform recording itself yet.

This matches the blueprint notion of optional data storage for commands like `diff`.

### Language Split and Future C++ Integration

- **Current state (Python-first)**:
  - CLI, orchestration, analysis, and reporting are implemented in Python.
  - ROS 2 interaction uses `rclpy` and focuses on introspection APIs described in the ROS 2 docs.
- **Planned C++ additions**:
  - Performance-critical data collection (fine-grained tracing, DDS-level QoS and transport analysis).
  - Tight integration with `ros2_tracing` using `rclcpp` and C++ libraries.

The module boundaries (separate files per feature, clear separation between data collection and rendering) are chosen so C++ backends can replace or augment specific data collection and analysis steps without changing the CLI surface.

