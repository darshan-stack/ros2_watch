robowatch Workflows
====================

This document describes how the main robowatch commands execute, following the blueprint's workflow guidance and aligning with ROS 2 concepts as documented in `https://github.com/ros2/ros2_documentation` and `https://docs.ros.org/en`.

### Common Workflow Pattern

All commands follow a shared high-level pattern:

1. User runs a `robowatch` command.
2. Core CLI parses the command and options and dispatches to a feature module.
3. The feature module uses the ROS2 Interaction Layer to collect raw data from the live ROS 2 system or from MCAP files.
4. The feature's analysis logic derives metrics, classifications, and findings.
5. The reporting logic formats results into terminal-friendly tables and messages.

This mirrors the pulse workflow sequence described in the technical blueprint.

### robowatch pulse

Goal: unified system health snapshot.

Workflow:

1. **User invocation**: `python -m robowatch pulse --duration 2.0`.
2. **Command parsing**: `cli.py` parses options and calls `run_pulse` in `pulse.py`.
3. **Data collection**:
   - Creates `GraphIntrospectionNode` and spins for the observation window.
   - Uses ROS 2 graph APIs to collect node and topic information.
   - Uses `psutil` to capture CPU and RAM usage for the host system.
4. **Analysis**:
   - Classifies nodes as active or zombie candidates based on topic connectivity.
   - Classifies topics as alive, no_subscribers, no_publishers, or idle.
   - Aggregates system resource usage.
5. **Reporting**:
   - Renders node and topic tables using `rich`.
   - Prints CPU and RAM summary and a note about future pipeline latency integration.

This implements the blueprint pulse workflow using only Python and ROS 2 graph introspection as a first stage. A future enhancement will insert a short-duration tracing session using `ros2_tracing` to compute end-to-end latencies.

### robowatch watch

Goal: live node monitoring with QoS awareness.

Workflow:

1. **User invocation**: `python -m robowatch watch /my_node --refresh 1.0`.
2. **Command parsing**: `cli.py` parses options and calls `run_watch` in `watch.py`.
3. **Data collection**:
   - Creates `WatchIntrospectionNode`.
   - Queries the ROS 2 graph for node names/namespaces and validates the target node.
   - For each topic, gathers publisher and subscription endpoint info and their QoS profiles.
   - Uses `psutil` to measure CPU and memory for the process.
4. **Analysis**:
   - Compares QoS profiles for pairs of publishers and subscribers attached to the same node.
   - Produces human-readable explanations for mismatches (reliability, durability, history, depth).
5. **Reporting (looped)**:
   - Clears the terminal and prints node-level CPU and memory.
   - Shows a table of QoS mismatches (or a “none detected” message).
   - Waits for `refresh_interval` seconds and repeats.

This aligns with the blueprint’s QoS mismatch detection and node performance monitoring, using ROS 2 QoS concepts described in the documentation.

### robowatch trace

Goal: end-to-end message tracing along a topic chain with latency estimation.

Workflow:

1. **User invocation**: `python -m robowatch trace "/camera/image -> /processed -> /cmd_vel" --duration 5.0`.
2. **Command parsing**: `cli.py` parses the chain string and duration and calls `run_trace` in `trace_cmd.py`.
3. **Data collection**:
   - Parses the topic chain into an ordered list of topics.
   - Creates `TraceNode` with subscriptions on each topic in the chain.
   - Spins for the requested duration, recording receipt timestamps per topic.
4. **Analysis**:
   - For each adjacent topic pair, computes hop latencies from aligned timestamp sequences.
   - Computes total average and maximum latency across the chain.
5. **Reporting**:
   - Displays a hop-by-hop latency table and a summary of total latency.
   - Notes that this is an approximation based on subscription timestamps and that a C++ `ros2_tracing` backend can later provide precise pipeline reconstruction.

This is an intermediate workflow that implements the trace blueprint concept without requiring kernel-level tracing, consistent with a quick, ROS 2-friendly CLI experience.

### robowatch diff

Goal: behavioral regression analysis between two runs.

Workflow:

1. **User invocation**: `python -m robowatch diff run_a.mcap run_b.mcap`.
2. **Command parsing**: `cli.py` calls `run_diff` in `diff_cmd.py`.
3. **Data collection**:
   - Opens both MCAP files with `mcap.reader.make_reader`.
   - Iterates messages, counting them per topic and tracking the first and last timestamps.
4. **Analysis**:
   - For each topic, computes message frequency for each run.
   - Compares frequencies to derive absolute and percentage deltas.
   - Flags missing topics and large percentage changes as potential regressions.
5. **Reporting**:
   - Renders a table with per-topic frequencies and delta descriptions.

This matches the blueprint’s regression analyzer and threshold-based reporting using MCAP as the data source.

### robowatch doctor

Goal: enhanced system audit with actionable fixes.

Workflow:

1. **User invocation**: `python -m robowatch doctor --deep`.
2. **Command parsing**: `cli.py` calls `run_doctor` in `doctor.py` with `deep=True`.
3. **Data collection**:
   - Creates `DoctorNode`.
   - Uses ROS 2 graph APIs to inspect nodes and topics.
4. **Analysis**:
   - Detects topics with publishers but no subscribers and the inverse.
   - Adds an issue if the graph appears empty (no nodes visible).
   - Associates each issue with a severity and plain-language recommendation.
5. **Reporting**:
   - Prints an issues table (severity, summary, recommendation).
   - When `--deep` is set, prints a note about extending the audit with DDS, tracing, and performance profiling.

This is an initial implementation of the blueprint’s health rule engine and actionable fixes, grounded in common ROS 2 troubleshooting steps.

