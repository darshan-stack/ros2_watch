import sys
from typing import Optional

import typer
from rich.console import Console

from .pulse import run_pulse
from .watch import run_watch
from .trace_cmd import run_trace
from .diff_cmd import run_diff
from .doctor import run_doctor


app = typer.Typer(help="robowatch - unified ROS2 health and debug CLI.")

console = Console()


@app.callback()
def main(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output.",
    ),
) -> None:
    if verbose:
        console.print("Verbose mode is enabled.")


@app.command()
def pulse(
    duration: float = typer.Option(
        2.0,
        "--duration",
        "-d",
        help="Observation window in seconds for collecting a health snapshot.",
    ),
    refresh: Optional[float] = typer.Option(
        None,
        "--refresh",
        "-r",
        help="If set, continuously refresh the snapshot every N seconds.",
    ),
) -> None:
    """
    Show a single-command system health snapshot.
    """
    try:
        run_pulse(duration=duration, refresh_interval=refresh)
    except KeyboardInterrupt:
        console.print("Interrupted by user.")
        raise typer.Exit(code=130) from None
    except RuntimeError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from None
    except Exception as exc:
        console.print(f"[bold red]Unexpected error:[/bold red] {exc}")
        raise typer.Exit(code=1) from None


@app.command()
def watch(
    node_name: str = typer.Argument(..., help="Name of the node to monitor."),
    refresh: float = typer.Option(
        1.0,
        "--refresh",
        "-r",
        help="Refresh interval in seconds for updating node statistics.",
    ),
) -> None:
    """
    Live monitoring of a specific node with QoS awareness.
    """
    try:
        run_watch(node_name=node_name, refresh_interval=refresh)
    except KeyboardInterrupt:
        console.print("Interrupted by user.")
        raise typer.Exit(code=130) from None
    except RuntimeError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from None
    except Exception as exc:
        console.print(f"[bold red]Unexpected error:[/bold red] {exc}")
        raise typer.Exit(code=1) from None


@app.command()
def trace(
    topic_chain: str = typer.Argument(
        ...,
        help="Topic chain, e.g. /camera/image->/processed->/cmd_vel.",
    ),
    duration: float = typer.Option(
        5.0,
        "--duration",
        "-d",
        help="Duration in seconds to observe and estimate hop-by-hop latency.",
    ),
) -> None:
    """
    End-to-end tracing of a message flow through a topic chain.
    """
    try:
        run_trace(topic_chain=topic_chain, duration=duration)
    except KeyboardInterrupt:
        console.print("Interrupted by user.")
        raise typer.Exit(code=130) from None
    except RuntimeError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from None
    except Exception as exc:
        console.print(f"[bold red]Unexpected error:[/bold red] {exc}")
        raise typer.Exit(code=1) from None


@app.command()
def diff(
    bag_file_1: str = typer.Argument(..., help="First bag/MCAP file."),
    bag_file_2: str = typer.Argument(..., help="Second bag/MCAP file."),
) -> None:
    """
    Behavioral regression analysis between two recordings.
    """
    try:
        run_diff(bag_path_a=bag_file_1, bag_path_b=bag_file_2)
    except RuntimeError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from None
    except Exception as exc:
        console.print(f"[bold red]Unexpected error:[/bold red] {exc}")
        raise typer.Exit(code=1) from None


@app.command()
def doctor(
    deep: bool = typer.Option(
        False,
        "--deep",
        help="Run a deep system audit with actionable recommendations.",
    )
) -> None:
    """
    System audit and recommendations.
    """
    try:
        run_doctor(deep=deep)
    except RuntimeError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from None
    except Exception as exc:
        console.print(f"[bold red]Unexpected error:[/bold red] {exc}")
        raise typer.Exit(code=1) from None


if __name__ == "__main__":
    sys.exit(app())

