robowatch CLI - Unified ROS2 Health and Debug Tool
==================================================

robowatch is a command-line tool for unified, real-time diagnostics and health monitoring of ROS2-based robotic systems.

The goal is to reduce debugging time, improve system reliability, and accelerate development cycles by consolidating fragmented debugging tasks and offering actionable insights.

### Features

- **pulse**: Single-command system health snapshot (nodes, topics, basic resource usage, and a high-level pipeline overview).
- **watch**: Live monitoring of a specific node with QoS awareness and basic resource metrics.
- **trace**: End-to-end tracing approximation of message flows through topic chains, reporting hop-by-hop and total latency based on subscription timestamps.
- **diff**: Behavioral regression analysis between two MCAP recordings focused on topic frequencies.
- **doctor**: System audit that highlights common graph-level issues and suggests fixes.

### Status

All top-level commands are wired and functional in a Python-first implementation. Deep DDS and ros2_tracing integration points are structured so they can be extended later with C++ backends.

### Requirements

- A working ROS2 installation (e.g., Humble, Iron, or Rolling) with `rclpy` available in the active Python environment.
- Python 3.10+ recommended.

Python dependencies are listed in `requirements.txt`. Some ROS2-related packages such as `rclpy` are usually provided by the ROS2 installation itself rather than installed via `pip`.

### Installation (development)

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Ensure that your ROS2 environment is sourced before running robowatch so that `rclpy` and ROS middleware are available:

```bash
source /opt/ros/humble/setup.bash  # adjust for your ROS2 distro
```

### Usage

From the project root, after activating your virtual environment and sourcing ROS2:

```bash
python -m robowatch pulse
python -m robowatch watch /my_node
python -m robowatch trace "/camera/image -> /processed -> /cmd_vel"
python -m robowatch diff run_a.mcap run_b.mcap
python -m robowatch doctor --deep
```

### Project Structure

- `robowatch/`: Python package containing CLI entry points and core modules.
- `tests/`: Basic unit tests.
- `requirements.txt`: Python dependencies for the robowatch CLI.
- `README.md`: Project overview and usage instructions.

See also:

- `ARCHITECTURE.md` for a detailed mapping of modules to the robowatch blueprint and ROS 2 concepts.
- `WORKFLOWS.md` for command-by-command workflow descriptions.

### Testing

Basic unit tests cover non-ROS2 specific logic and can be run with:

```bash
pytest
```

