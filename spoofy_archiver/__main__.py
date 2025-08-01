"""Main CLI for Entry Point."""

import argparse
from pathlib import Path

from spoofy_archiver import __version__, cli
from spoofy_archiver.utils import SERVICE_NAME
from spoofy_archiver.utils.logger import get_logger, setup_logger

logger = get_logger(__name__)


def main() -> None:
    """Main."""
    logger.debug("Starting up cli")

    logger.info("Spoofy Archiver version %s", __version__)

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-v",
        help="Debug level logging",
        action="store_true",
    )
    arg_parser.add_argument(
        "-vv",
        help="Trace level logging",
        action="store_true",
    )
    arg_parser.add_argument(
        "-o",
        "--output",
        help="Set the target directory for downloaded albums",
        default="output",
    )
    arg_parser.add_argument(
        "--delay",
        help="Set the delay between downloads, will be offset by a proportional random amount",
        type=int,
        default=30,
    )
    arg_parser.add_argument(
        "--interactive",
        help="Run in interactive mode, will not handle URLs, useful for using alternate login options.",
        action="store_true",
        default=False,
    )
    arg_parser.add_argument(  # Positional argument
        "url",
        help=f"URL of {SERVICE_NAME} Album/Track/Artist, if not specified this program will download all liked albums.",
        nargs="?",
        default=None,
    )

    args = arg_parser.parse_args()

    output_directory_as_path = Path(args.output)

    logger.info("Target directory: %s", output_directory_as_path)
    logger.info("Download delay (seconds): %s + small random offset", args.delay)

    if args.vv:
        setup_logger(log_level="TRACE")
    elif args.v:
        setup_logger(log_level="DEBUG")
    else:
        setup_logger(log_level="INFO")

    if args.interactive:
        cli.interactive(output_directory_as_path, args.delay)
    else:
        cli.noninteractive(output_directory_as_path, args.delay, args.url)


if __name__ == "__main__":
    main()
