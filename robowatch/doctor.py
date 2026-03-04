from dataclasses import dataclass
from typing import List

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
class DoctorIssue:
    severity: str
    summary: str
    recommendation: str


class DoctorNode(Node):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__("robowatch_doctor")


def _ensure_rclpy_available() -> None:
    if rclpy is None:
        raise RuntimeError(
            "rclpy is not available. Ensure your ROS2 environment is sourced "
            "and that rclpy is installed for this Python interpreter."
        )


def _basic_checks(node: Node) -> List[DoctorIssue]:  # type: ignore[name-defined]
    issues: List[DoctorIssue] = []

    topic_names_and_types = node.get_topic_names_and_types()
    for topic_name, _topic_types in topic_names_and_types:
        pubs = node.get_publishers_info_by_topic(topic_name)
        subs = node.get_subscriptions_info_by_topic(topic_name)
        if pubs and not subs:
            issues.append(
                DoctorIssue(
                    severity="warning",
                    summary=f"Topic {topic_name} has publishers but no subscribers.",
                    recommendation="Verify that all expected consumers are launched and using matching topic names.",
                )
            )
        if subs and not pubs:
            issues.append(
                DoctorIssue(
                    severity="warning",
                    summary=f"Topic {topic_name} has subscribers but no publishers.",
                    recommendation="Check that the producing node is running and configured with the same topic name.",
                )
            )

    node_names_and_namespaces = node.get_node_names_and_namespaces()
    if not node_names_and_namespaces:
        issues.append(
            DoctorIssue(
                severity="error",
                summary="No nodes detected in the ROS2 graph.",
                recommendation="Ensure that your ROS2 environment is sourced and that at least one node is running.",
            )
        )

    return issues


def run_doctor(deep: bool) -> None:
    _ensure_rclpy_available()

    rclpy.init(args=None)
    try:
        node = DoctorNode()
        issues = _basic_checks(node)

        console.rule("[bold cyan]robowatch doctor[/bold cyan]")

        if not issues:
            console.print("No obvious issues detected in the current ROS2 graph.")
            return

        table = Table(title="Detected issues", show_lines=False)
        table.add_column("Severity")
        table.add_column("Summary")
        table.add_column("Recommendation")

        for issue in issues:
            table.add_row(issue.severity, issue.summary, issue.recommendation)

        console.print()
        console.print(table)

        if deep:
            console.print()
            console.print(
                "Deep analysis hooks can be extended to integrate DDS-level checks, "
                "ros2_tracing data, and performance profiling."
            )
    finally:
        rclpy.shutdown()

