from typing import List

from ros2cli.command import CommandExtension  # type: ignore[import]

from .cli import app


class RobowatchCommand(CommandExtension):
    """ros2 robowatch command entry point.

    This allows running robowatch as a ROS 2 CLI extension:

        ros2 robowatch pulse
        ros2 robowatch watch /my_node
        ros2 robowatch trace "/camera/image -> /processed -> /cmd_vel"
        ros2 robowatch diff run_a.mcap run_b.mcap
        ros2 robowatch doctor --deep
    """

    def add_arguments(self, parser, cli_name: str) -> None:  # type: ignore[override]
        # Accept all remaining arguments and forward them to the Typer app.
        parser.add_argument("robowatch_args", nargs="*")

    def main(self, *, parser, args) -> int:  # type: ignore[override]
        argv: List[str] = list(args.robowatch_args)
        # Delegate to the Typer CLI, using "ros2 robowatch" as the program name.
        app(prog_name=f"{parser.prog} robowatch", args=argv)
        return 0

