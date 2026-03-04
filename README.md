# ros2_watch

** ROS2 Health and Debug CLI**

ros2_watch is a command-line tool that replaces the scattered workflow of running
`ros2 node list`, `ros2 topic hz`, `ros2 doctor`, `htop`, and custom scripts one
by one. Instead, a single entry point gives you a complete, real-time picture of
your ROS2 system — nodes, topics, QoS, resources, latency, and graph issues —
all in one place.

---

## The Problem

Debugging a ROS2 robot typically looks like this:

```
ros2 node list
ros2 topic list
ros2 topic hz /scan
ros2 topic info /scan --verbose
ros2 doctor
htop
```

Six commands. Six terminals. And you still have to piece the information together
manually. ros2_watch collapses all of that into one command.

---

## Commands

### pulse

Single-command system health snapshot.

```
ros2_watch pulse
ros2_watch pulse --watch
ros2_watch pulse --json
ros2_watch pulse --export report.json
```

Shows every active node with CPU and RAM usage, every topic with live Hz and QoS
settings, zombie nodes, stale topics, graph connectivity issues, and TF tree health.
All at once, in a single terminal view.

---

### watch

Live monitoring of a specific node.

```
ros2_watch watch /camera_node
ros2_watch watch /slam_node --rate 2.0
ros2_watch watch /move_base --qos
ros2_watch watch /camera_node --alert-hz 25
```

Shows the node's PID, CPU and RAM in real time, all published and subscribed topics
with live Hz, full QoS profiles per topic (with --qos), and an alert when publish
rate drops below a threshold.

---

### trace

End-to-end latency tracing through a topic pipeline.

```
ros2_watch trace "/camera/image_raw -> /processed/image -> /cmd_vel"
ros2_watch trace "/scan -> /costmap -> /move_base/goal" --duration 30
ros2_watch trace "/camera/image_raw -> /cmd_vel" --histogram
ros2_watch trace "/lidar -> /slam/pose -> /odom" --export trace.json
```

Subscribes to each topic in the chain and records message arrival timestamps.
For each hop, it matches the nearest downstream message and computes median
latency and jitter. Reports per-hop and total end-to-end latency, with an
optional ASCII histogram of the latency distribution.

---

### diff

Behavioral regression analysis between two MCAP recordings.

```
ros2_watch diff baseline.mcap new_run.mcap
ros2_watch diff run_a.mcap run_b.mcap --topics /scan /odom /cmd_vel
ros2_watch diff run_a.mcap run_b.mcap --threshold 0.05
ros2_watch diff run_a.mcap run_b.mcap --report
```

Reads both bag files, computes average publish Hz per topic in each, and flags
topics where the frequency has changed beyond the threshold (default 15 percent).
Useful for catching performance regressions after software updates or configuration
changes. The --report flag generates a standalone HTML file.

---

### doctor

Full ROS2 graph audit with actionable fix suggestions.

```
ros2_watch doctor
ros2_watch doctor --deep
ros2_watch doctor --fix
ros2_watch doctor --export audit.json
```

Standard audit checks:

- Zombie nodes visible in the graph but not responding
- QoS mismatches where publisher and subscriber profiles are incompatible
- Unconnected topics with publishers but no subscribers, or vice versa
- TF tree integrity and publish rate
- System resource limits
- Topic naming issues

Deep audit adds:

- DDS middleware configuration inspection
- Lifecycle node state checks
- Parameter server consistency

The --fix flag attempts safe auto-fixes: restarting the ROS2 daemon for zombie
nodes, and calling `ros2 lifecycle set activate` for inactive lifecycle nodes.

---

### replay

Step-through MCAP bag file debugger.

```
ros2_watch replay recording.mcap --step
ros2_watch replay recording.mcap --step --topic /camera/image_raw
ros2_watch replay recording.mcap --speed 2.0
```

In step mode, press Enter to advance to the next message, type `s` to skip 10
messages, or `q` to quit. Each message shows its topic, type, timestamp, and
size. Useful for inspecting exactly what was published and when, without replaying
the entire bag at full speed.

---

### anomaly

AI-powered anomaly detection on topic frequency patterns.

```
ros2_watch anomaly --train baseline.mcap
ros2_watch anomaly --train baseline.mcap --watch
ros2_watch anomaly --model robowatch_model --watch
ros2_watch anomaly --model robowatch_model --watch --sensitivity 3.0
```

Trains a statistical baseline from a known-good MCAP recording, then monitors
the live system for deviations. Uses Z-score per topic for univariate detection
and IsolationForest for multivariate pattern anomalies that span multiple topics
simultaneously. Anomalies are classified as INFO (greater than 2 sigma), WARNING
(greater than 3 sigma), or CRITICAL (greater than 4 sigma).

---

### web

Live browser dashboard over WebSocket.

```
ros2_watch web
ros2_watch web --port 9090
ros2_watch web --host 0.0.0.0
ros2_watch web --open
```

Starts a FastAPI server that pushes system state to the browser every 1.5 seconds.
The dashboard shows live sparkline charts per topic, node list with CPU per node,
topic list with Hz badges, system metrics, and a real-time issues panel. The
--host 0.0.0.0 flag makes it accessible from another machine on the same network,
which is useful when the robot is headless.

---

## Installation

From source, during development:

```
git clone https://github.com/darshan-stack/ros2_watch
cd ros2_watch
pip install -e .
```

From PyPI (once published):

```
pip install ros2-watch
```

With AI anomaly detection support:

```
pip install ros2-watch[ai]
```

Source your ROS2 environment before running:

```
source /opt/ros/humble/setup.bash
```

---

## Requirements

- Python 3.10 or higher
- ROS2 Humble, Iron, or Rolling with rclpy available in the Python environment
- See requirements.txt for Python package dependencies

ros2_watch operates in three modes depending on what is available. If rclpy
initializes successfully it uses direct Python bindings to the ROS2 graph. If
rclpy is unavailable it falls back to subprocess-based queries using the ros2
command-line tools. In testing environments it runs in mock mode with synthetic
data, requiring no ROS2 installation at all.

---

## Project Structure

```
ros2_watch/
    robowatch/
        __main__.py          CLI entry point and argument dispatch
        core/
            ros2_interface.py    ROS2 graph interaction, Hz tracking, QoS analysis
            terminal_ui.py       Rich terminal rendering
            banner.py            ASCII banner
        commands/
            pulse.py
            watch.py
            trace.py
            diff.py
            doctor.py
            replay.py
            anomaly.py
        ai/
            anomaly_detector.py  Z-score and IsolationForest detection
        web/
            app.py               FastAPI app, WebSocket, dashboard HTML
            server.py            CLI entry for web command
        plugins/
            __init__.py          Plugin base class and registry
    tests/
        test_core.py             Unit tests, no ROS2 required
    .github/
        workflows/
            ci.yml               Lint, test matrix, PyPI publish
    pyproject.toml
    requirements.txt
    ARCHITECTURE.md
    WORKFLOWS.md
```

Full technical documentation is in ARCHITECTURE.md. Command-by-command workflow
guides with examples are in WORKFLOWS.md.

---

## Plugin System

ros2_watch doctor can be extended with custom health checks:

```python
from robowatch.plugins import RobowatchPlugin, register_plugin

class BatteryCheck(RobowatchPlugin):
    name = "battery_check"

    def run(self, health) -> list[dict]:
        issues = []
        for topic in health.topics:
            if "battery" in topic.name and topic.hz < 0.5:
                issues.append({
                    "severity": "WARNING",
                    "component": topic.name,
                    "message": f"Battery topic publishing at {topic.hz:.1f} Hz",
                    "fix": "Check battery monitoring node",
                })
        return issues

register_plugin(BatteryCheck())
```

Plugins receive the full SystemHealth dataclass and return a list of issue dicts
with severity, component, message, and fix fields.

---

## Testing

Unit tests cover core logic without requiring a running ROS2 system:

```
pytest tests/ -v
pytest tests/ --cov=ros2_watch --cov-report=html
```

CI runs on Python 3.10, 3.11, and 3.12. A separate integration job runs against
ROS2 Humble on Ubuntu 22.04.

---

## Contributing

1. Fork the repository and clone it locally
2. Run `pip install -e ".[dev]"` to install development dependencies
3. Make your changes
4. Run `ruff check ros2_watch/` and `pytest tests/` before submitting
5. Open a pull request against the main branch

Bug reports, feature requests, and real-world testing on actual robot hardware
are all welcome via GitHub Issues.

---

## License

Apache License 2.0. See LICENSE for the full text.

---

## Links

- Repository: https://github.com/darshan-stack/ros2_watch

- Issue tracker: https://github.com/darshan-stack/ros2_watch/issues
