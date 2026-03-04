from robowatch.pulse import TopicInfo, NodeInfo, SystemResources, PulseSnapshot


def test_topic_info_status():
    assert TopicInfo(name="/a", types=(), publishers=1, subscriptions=1).status == "alive"
    assert TopicInfo(name="/a", types=(), publishers=1, subscriptions=0).status == "no_subscribers"
    assert TopicInfo(name="/a", types=(), publishers=0, subscriptions=1).status == "no_publishers"
    assert TopicInfo(name="/a", types=(), publishers=0, subscriptions=0).status == "idle"


def test_node_info_status():
    assert NodeInfo(name="n", namespace="/", topic_count=1).status == "active"
    assert NodeInfo(name="n", namespace="/", topic_count=0).status == "zombie_candidate"


def test_pulse_snapshot_dataclass():
    resources = SystemResources(cpu_percent=10.0, ram_percent=20.0)
    snapshot = PulseSnapshot(
        topics=[],
        nodes=[],
        resources=resources,
        observation_window=1.0,
    )
    assert snapshot.resources.cpu_percent == 10.0
    assert snapshot.observation_window == 1.0

