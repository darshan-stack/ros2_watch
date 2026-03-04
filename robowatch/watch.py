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
class QoSMismatch:
    topic_name: str
    publisher_qos: str
    subscription_qos: str
    explanation: str


@dataclass
class NodeStats:
    node_name: str
    namespace: str
    cpu_percent: float
    memory_mb: float
    qos_mismatches: List[QoSMismatch]


class WatchIntrospectionNode(Node):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__("robowatch_watch")


def _ensure_rclpy_available() -> None:
    if rclpy is None:
        raise RuntimeError(
            "rclpy is not available. Ensure your ROS2 environment is sourced "
            "and that rclpy is installed for this Python interpreter."
        )


def _format_qos_profile(qos) -> str:
    parts = []
    if hasattr(qos, "reliability"):
        parts.append(f"rel={qos.reliability.name}")
    if hasattr(qos, "durability"):
        parts.append(f"dur={qos.durability.name}")
    if hasattr(qos, "history"):
        parts.append(f"hist={qos.history.name}")
    if hasattr(qos, "depth"):
        parts.append(f"depth={qos.depth}")
    return ",".join(parts) if parts else "unknown"


def _compare_qos(publisher_qos, subscription_qos) -> Optional[str]:
    explanation_parts: List[str] = []

    if hasattr(publisher_qos, "reliability") and hasattr(subscription_qos, "reliability"):
        if publisher_qos.reliability != subscription_qos.reliability:
            explanation_parts.append("reliability mismatch")

    if hasattr(publisher_qos, "durability") and hasattr(subscription_qos, "durability"):
        if publisher_qos.durability != subscription_qos.durability:
            explanation_parts.append("durability mismatch")

    if hasattr(publisher_qos, "history") and hasattr(subscription_qos, "history"):
        if publisher_qos.history != subscription_qos.history:
            explanation_parts.append("history mismatch")

    if hasattr(publisher_qos, "depth") and hasattr(subscription_qos, "depth"):
        if publisher_qos.depth < subscription_qos.depth:
            explanation_parts.append("publisher depth lower than subscriber depth")

    if not explanation_parts:
        return None

    return "; ".join(explanation_parts)


def collect_node_stats(target_node: str) -> NodeStats:
    _ensure_rclpy_available()

    rclpy.init(args=None)
    try:
        node = WatchIntrospectionNode()

        node_names_and_namespaces = node.get_node_names_and_namespaces()
        matching = [item for item in node_names_and_namespaces if item[0] == target_node]
        if not matching:
            raise RuntimeError(f"Node {target_node} not found in ROS graph.")

        node_name, namespace = matching[0]

        qos_mismatches: List[QoSMismatch] = []

        topic_names_and_types = node.get_topic_names_and_types()
        for topic_name, _topic_types in topic_names_and_types:
            publishers = node.get_publishers_info_by_topic(topic_name)
            subscriptions = node.get_subscriptions_info_by_topic(topic_name)

            publishers = [p for p in publishers if p.node_name == node_name]
            subscriptions = [s for s in subscriptions if s.node_name == node_name]

            for pub in publishers:
                for sub in subscriptions:
                    qos_pub = pub.qos_profile
                    qos_sub = sub.qos_profile
                    explanation = _compare_qos(qos_pub, qos_sub)
                    if explanation is not None:
                        qos_mismatches.append(
                            QoSMismatch(
                                topic_name=topic_name,
                                publisher_qos=_format_qos_profile(qos_pub),
                                subscription_qos=_format_qos_profile(qos_sub),
                                explanation=explanation,
                            )
                        )

        proc = psutil.Process()
        cpu_percent = proc.cpu_percent(interval=0.1)
        mem_info = proc.memory_info()
        memory_mb = mem_info.rss / (1024 * 1024)

        return NodeStats(
            node_name=node_name,
            namespace=namespace,
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            qos_mismatches=qos_mismatches,
        )
    finally:
        rclpy.shutdown()


def render_node_stats(stats: NodeStats) -> None:
    console.rule("[bold cyan]robowatch watch[/bold cyan]")

    console.print(
        f"Node: [bold]{stats.node_name}[/bold] | Namespace: {stats.namespace or '/'} | "
        f"CPU: {stats.cpu_percent:.1f}% | Memory: {stats.memory_mb:.1f} MiB"
    )

    table = Table(title="QoS mismatches", show_lines=False)
    table.add_column("Topic", style="bold")
    table.add_column("Publisher QoS")
    table.add_column("Subscriber QoS")
    table.add_column("Explanation")

    if not stats.qos_mismatches:
        console.print()
        console.print("No QoS mismatches detected for this node.")
        return

    for mismatch in stats.qos_mismatches:
        table.add_row(
            mismatch.topic_name,
            mismatch.publisher_qos,
            mismatch.subscription_qos,
            mismatch.explanation,
        )

    console.print()
    console.print(table)


def run_watch(node_name: str, refresh_interval: float) -> None:
    if refresh_interval <= 0:
        raise RuntimeError("Refresh interval must be positive.")

    while True:
        stats = collect_node_stats(target_node=node_name)
        console.clear()
        render_node_stats(stats)
        time.sleep(refresh_interval)

