import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import psutil
from rich.console import Console
from rich.table import Table

try:
    import rclpy
    from rclpy.node import Node
except ImportError:  # type: ignore[no-redef]
    rclpy = None  # type: ignore[assignment]
    Node = object  # type: ignore[assignment]


console = Console()


@dataclass
class TopicInfo:
    name: str
    types: Tuple[str, ...]
    publishers: int
    subscriptions: int

    @property
    def status(self) -> str:
        if self.publishers > 0 and self.subscriptions > 0:
            return "alive"
        if self.publishers > 0 and self.subscriptions == 0:
            return "no_subscribers"
        if self.publishers == 0 and self.subscriptions > 0:
            return "no_publishers"
        return "idle"


@dataclass
class NodeInfo:
    name: str
    namespace: str
    topic_count: int

    @property
    def status(self) -> str:
        if self.topic_count > 0:
            return "active"
        return "zombie_candidate"


@dataclass
class SystemResources:
    cpu_percent: float
    ram_percent: float


@dataclass
class PulseSnapshot:
    topics: List[TopicInfo]
    nodes: List[NodeInfo]
    resources: SystemResources
    observation_window: float


class GraphIntrospectionNode(Node):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__("robowatch_pulse")


def _ensure_rclpy_available() -> None:
    if rclpy is None:
        raise RuntimeError(
            "rclpy is not available. Ensure your ROS2 environment is sourced "
            "and that rclpy is installed for this Python interpreter."
        )


def collect_system_resources() -> SystemResources:
    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory().percent
    return SystemResources(cpu_percent=cpu, ram_percent=ram)


def collect_ros_graph_snapshot(observation_window: float) -> Tuple[List[NodeInfo], List[TopicInfo]]:
    _ensure_rclpy_available()

    rclpy.init(args=None)
    try:
        node = GraphIntrospectionNode()

        start = time.time()
        while time.time() - start < observation_window:
            rclpy.spin_once(node, timeout_sec=0.1)

        node_descriptors = node.get_node_names_and_namespaces()
        topic_names_and_types = node.get_topic_names_and_types()

        topic_infos: List[TopicInfo] = []
        for topic_name, topic_types in topic_names_and_types:
            publishers = node.get_publishers_info_by_topic(topic_name)
            subscriptions = node.get_subscriptions_info_by_topic(topic_name)
            topic_infos.append(
                TopicInfo(
                    name=topic_name,
                    types=tuple(topic_types),
                    publishers=len(publishers),
                    subscriptions=len(subscriptions),
                )
            )

        node_topic_counts: Dict[Tuple[str, str], int] = {}
        for info in topic_infos:
            pubs = node.get_publishers_info_by_topic(info.name)
            subs = node.get_subscriptions_info_by_topic(info.name)
            for endpoint in list(pubs) + list(subs):
                key = (endpoint.node_name, endpoint.node_namespace)
                node_topic_counts[key] = node_topic_counts.get(key, 0) + 1

        node_infos: List[NodeInfo] = []
        for name, namespace in node_descriptors:
            count = node_topic_counts.get((name, namespace), 0)
            node_infos.append(NodeInfo(name=name, namespace=namespace, topic_count=count))

        return node_infos, topic_infos
    finally:
        rclpy.shutdown()


def build_pulse_snapshot(observation_window: float) -> PulseSnapshot:
    nodes, topics = collect_ros_graph_snapshot(observation_window=observation_window)
    resources = collect_system_resources()
    return PulseSnapshot(
        topics=topics,
        nodes=nodes,
        resources=resources,
        observation_window=observation_window,
    )


def render_pulse_snapshot(snapshot: PulseSnapshot) -> None:
    console.print()
    console.rule("[bold cyan]robowatch pulse[/bold cyan]")

    resources = snapshot.resources
    console.print(
        f"Observation window: {snapshot.observation_window:.1f}s | "
        f"CPU: {resources.cpu_percent:.1f}% | RAM: {resources.ram_percent:.1f}%"
    )

    node_table = Table(title="Nodes", show_lines=False)
    node_table.add_column("Name", style="bold")
    node_table.add_column("Namespace")
    node_table.add_column("Topics")
    node_table.add_column("Status")

    for node_info in sorted(snapshot.nodes, key=lambda n: (n.namespace, n.name)):
        node_table.add_row(
            node_info.name,
            node_info.namespace or "/",
            str(node_info.topic_count),
            node_info.status,
        )

    topic_table = Table(title="Topics", show_lines=False)
    topic_table.add_column("Name", style="bold")
    topic_table.add_column("Types")
    topic_table.add_column("Pubs")
    topic_table.add_column("Subs")
    topic_table.add_column("Status")

    for topic in sorted(snapshot.topics, key=lambda t: t.name):
        topic_table.add_row(
            topic.name,
            ", ".join(topic.types),
            str(topic.publishers),
            str(topic.subscriptions),
            topic.status,
        )

    console.print()
    console.print(node_table)
    console.print()
    console.print(topic_table)
    console.print()

    console.print(
        "Note: End-to-end pipeline latency is not yet implemented in this early pulse version."
    )


def run_pulse(duration: float, refresh_interval: Optional[float]) -> None:
    if duration <= 0:
        raise RuntimeError("Duration must be positive.")
    if refresh_interval is not None and refresh_interval <= 0:
        raise RuntimeError("Refresh interval must be positive when provided.")

    if refresh_interval is None:
        snapshot = build_pulse_snapshot(observation_window=duration)
        render_pulse_snapshot(snapshot)
        return

    while True:
        snapshot = build_pulse_snapshot(observation_window=duration)
        console.clear()
        render_pulse_snapshot(snapshot)
        time.sleep(refresh_interval)

