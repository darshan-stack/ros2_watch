from pathlib import Path

from robowatch.diff_cmd import TopicMetrics, _compare_metrics


def test_topic_metrics_frequency():
    m = TopicMetrics(topic="/a", message_count=11, duration_sec=10.0)
    assert abs(m.frequency_hz - 1.0) < 1e-6


def test_compare_metrics_handles_missing_topics(tmp_path: Path):
    a = {"/a": TopicMetrics(topic="/a", message_count=1, duration_sec=0.0)}
    b = {}
    rows = _compare_metrics(a, b)
    assert len(rows) == 1
    assert rows[0]["topic"] == "/a"
    assert "topic missing" in rows[0]["delta"]

