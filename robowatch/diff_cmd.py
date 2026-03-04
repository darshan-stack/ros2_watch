from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from mcap.reader import make_reader  # type: ignore[import]
from rich.console import Console
from rich.table import Table


console = Console()


@dataclass
class TopicMetrics:
    topic: str
    message_count: int
    duration_sec: float

    @property
    def frequency_hz(self) -> float:
        if self.duration_sec <= 0 or self.message_count <= 1:
            return 0.0
        return (self.message_count - 1) / self.duration_sec


def _read_mcap_metrics(path: Path) -> Dict[str, TopicMetrics]:
    if not path.exists():
        raise RuntimeError(f"File not found: {path}")

    topic_counts: Dict[str, int] = {}
    topic_first_stamp: Dict[str, float] = {}
    topic_last_stamp: Dict[str, float] = {}

    with path.open("rb") as f:
        reader = make_reader(f)
        for schema, channel, message in reader.iter_messages():
            topic = channel.topic
            stamp = message.log_time / 1e9
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
            if topic not in topic_first_stamp:
                topic_first_stamp[topic] = stamp
            topic_last_stamp[topic] = stamp

    metrics: Dict[str, TopicMetrics] = {}
    for topic, count in topic_counts.items():
        first = topic_first_stamp.get(topic, 0.0)
        last = topic_last_stamp.get(topic, first)
        duration = max(0.0, last - first)
        metrics[topic] = TopicMetrics(topic=topic, message_count=count, duration_sec=duration)

    return metrics


def _compare_metrics(
    metrics_a: Dict[str, TopicMetrics],
    metrics_b: Dict[str, TopicMetrics],
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    topics = sorted(set(metrics_a.keys()) | set(metrics_b.keys()))

    for topic in topics:
        a = metrics_a.get(topic)
        b = metrics_b.get(topic)

        if a is None or b is None:
            rows.append(
                {
                    "topic": topic,
                    "freq_a": f"{a.frequency_hz:.2f}" if a else "-",
                    "freq_b": f"{b.frequency_hz:.2f}" if b else "-",
                    "delta": "topic missing in one run",
                }
            )
            continue

        delta = b.frequency_hz - a.frequency_hz
        percent = (delta / a.frequency_hz * 100.0) if a.frequency_hz > 0 else 0.0

        description = ""
        if abs(percent) > 10.0:
            if delta < 0:
                description = "significant drop in frequency"
            else:
                description = "significant increase in frequency"

        rows.append(
            {
                "topic": topic,
                "freq_a": f"{a.frequency_hz:.2f}",
                "freq_b": f"{b.frequency_hz:.2f}",
                "delta": f"{delta:.2f} Hz ({percent:.1f}%) {description}",
            }
        )

    return rows


def run_diff(bag_path_a: str, bag_path_b: str) -> None:
    path_a = Path(bag_path_a)
    path_b = Path(bag_path_b)

    metrics_a = _read_mcap_metrics(path_a)
    metrics_b = _read_mcap_metrics(path_b)

    rows = _compare_metrics(metrics_a, metrics_b)

    console.rule("[bold cyan]robowatch diff[/bold cyan]")
    console.print(f"File A: {path_a}")
    console.print(f"File B: {path_b}")

    table = Table(title="Topic frequency comparison", show_lines=False)
    table.add_column("Topic", style="bold")
    table.add_column("Freq A (Hz)")
    table.add_column("Freq B (Hz)")
    table.add_column("Delta / Comment")

    if not rows:
        console.print()
        console.print("No topics found in either MCAP file.")
        return

    for row in rows:
        table.add_row(row["topic"], row["freq_a"], row["freq_b"], row["delta"])

    console.print()
    console.print(table)

