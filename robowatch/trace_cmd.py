import time
from dataclasses import dataclass
from typing import Dict, List, Tuple

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
class HopLatency:
    source_topic: str
    target_topic: str
    avg_latency_ms: float
    max_latency_ms: float


@dataclass
class TraceResult:
    hops: List[HopLatency]
    total_avg_latency_ms: float
    total_max_latency_ms: float


class TraceNode(Node):  # type: ignore[misc]
    def __init__(self, topics: List[str]) -> None:
        super().__init__("robowatch_trace")
        self._topics = topics
        self._timestamps: Dict[str, List[float]] = {name: [] for name in topics}

        from rclpy.qos import QoSProfile

        qos = QoSProfile(depth=10)
        for topic in topics:
            self.create_subscription(
                msg_type=self._guess_msg_type(topic),
                topic=topic,
                callback=self._make_callback(topic),
                qos_profile=qos,
            )

    def _guess_msg_type(self, topic: str):
        from std_msgs.msg import Header  # type: ignore[import]

        return Header

    def _make_callback(self, topic: str):
        def _callback(msg) -> None:
            stamp = time.time()
            self._timestamps[topic].append(stamp)

        return _callback

    def get_timestamps(self) -> Dict[str, List[float]]:
        return self._timestamps


def _ensure_rclpy_available() -> None:
    if rclpy is None:
        raise RuntimeError(
            "rclpy is not available. Ensure your ROS2 environment is sourced "
            "and that rclpy is installed for this Python interpreter."
        )


def parse_topic_chain(topic_chain: str) -> List[str]:
    parts = [item.strip() for item in topic_chain.split("->")]
    topics = [p for p in parts if p]
    if len(topics) < 2:
        raise RuntimeError("Topic chain must contain at least a source and a destination topic.")
    return topics


def estimate_latency(chain: List[str], timestamps: Dict[str, List[float]]) -> TraceResult:
    hops: List[HopLatency] = []
    total_latencies: List[float] = []

    for i in range(len(chain) - 1):
        src = chain[i]
        dst = chain[i + 1]
        src_times = timestamps.get(src, [])
        dst_times = timestamps.get(dst, [])
        if not src_times or not dst_times:
            continue

        hop_latencies: List[float] = []
        for s, d in zip(src_times, dst_times):
            if d >= s:
                hop_latencies.append((d - s) * 1000.0)

        if not hop_latencies:
            continue

        avg_latency = sum(hop_latencies) / len(hop_latencies)
        max_latency = max(hop_latencies)
        hops.append(
            HopLatency(
                source_topic=src,
                target_topic=dst,
                avg_latency_ms=avg_latency,
                max_latency_ms=max_latency,
            )
        )
        total_latencies.extend(hop_latencies)

    total_avg = sum(total_latencies) / len(total_latencies) if total_latencies else 0.0
    total_max = max(total_latencies) if total_latencies else 0.0

    return TraceResult(hops=hops, total_avg_latency_ms=total_avg, total_max_latency_ms=total_max)


def render_trace_result(chain: List[str], result: TraceResult) -> None:
    console.rule("[bold cyan]robowatch trace[/bold cyan]")
    console.print("Topic chain: " + " -> ".join(chain))

    table = Table(title="Hop-by-hop latency", show_lines=False)
    table.add_column("Source")
    table.add_column("Target")
    table.add_column("Avg latency (ms)")
    table.add_column("Max latency (ms)")

    if not result.hops:
        console.print()
        console.print("No latency samples captured for the given chain.")
        return

    for hop in result.hops:
        table.add_row(
            hop.source_topic,
            hop.target_topic,
            f"{hop.avg_latency_ms:.2f}",
            f"{hop.max_latency_ms:.2f}",
        )

    console.print()
    console.print(table)
    console.print()
    console.print(
        f"Total avg latency: {result.total_avg_latency_ms:.2f} ms | "
        f"Total max latency: {result.total_max_latency_ms:.2f} ms"
    )
    console.print()
    console.print(
        "This approximation is based on local subscription timestamps and does not yet "
        "integrate ros2_tracing. For precise analysis, a C++ tracing backend can be added."
    )


def run_trace(topic_chain: str, duration: float) -> None:
    if duration <= 0:
        raise RuntimeError("Duration must be positive.")

    topics = parse_topic_chain(topic_chain)
    _ensure_rclpy_available()

    rclpy.init(args=None)
    try:
        node = TraceNode(topics=topics)
        start = time.time()
        while time.time() - start < duration:
            rclpy.spin_once(node, timeout_sec=0.1)

        timestamps = node.get_timestamps()
        result = estimate_latency(chain=topics, timestamps=timestamps)
        render_trace_result(chain=topics, result=result)
    finally:
        rclpy.shutdown()

