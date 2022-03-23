"""Main program for command line utility"""

import argparse
import logging as log
import sys

import voluptuous as vol  # type: ignore

from remoteprotocols import const
from remoteprotocols.registry import ProtocolRegistry

CMD_VALIDATE_PROTOCOL = "validate-protocol"
CMD_VALIDATE_COMMAND = "validate-command"
CMD_ENCODE = "encode"
CMD_LIST = "list"

REGISTRY = ProtocolRegistry()


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Converts command line arguments in an object"""

    options_parser = argparse.ArgumentParser(add_help=False)
    options_parser.add_argument(
        "-v", "--version", help="Show version information.", action="store_true"
    )
    parser = argparse.ArgumentParser(
        description=f"{const.PROGRAM_NAME} v{const.PROGRAM_VERSION}",
        parents=[options_parser],
    )

    subparsers = parser.add_subparsers(
        help="Command to run:", dest="command", metavar="command"
    )
    subparsers.required = True

    parser_config = subparsers.add_parser(
        CMD_VALIDATE_PROTOCOL, help="Validate a protocol definition file."
    )
    parser_config.add_argument("files", help="Your YAML definition file(s).", nargs="+")

    parser_config = subparsers.add_parser(
        CMD_VALIDATE_COMMAND, help="Validate a send command string(s)."
    )
    parser_config.add_argument("commands", help="Command(s) to validate.", nargs="+")

    parser_config = subparsers.add_parser(
        CMD_ENCODE, help="Encodes command string(s) into raw signal."
    )
    parser_config.add_argument("commands", help="Command(s) to encode.", nargs="+")

    parser_config = subparsers.add_parser(CMD_LIST, help="List supported protocols.")
    parser_config.add_argument(
        "-v",
        "--verbose",
        help="Include detailed description of the protocol.",
        action="store_true",
    )
    parser_config.add_argument(
        "protocols", help="Restrict list to specific arguments", nargs="*"
    )

    return parser.parse_args(argv[1:])


def cmd_validate_protocol(files: list[str]) -> int:
    """Runs validate-protocol command"""

    for file in files:

        try:
            REGISTRY.load(file)

        except vol.MultipleInvalid as errs:
            log.error("Invalid format in file %s", file)
            for err in errs.errors:
                log.error(err)
                # print(err.__dict__)
            return 1

        except vol.Invalid as err:
            log.error("Invalid format in file %s", file)
            log.error(err)
            return 1

    print("Protocol definitions are OK")
    return 0


def cmd_validate_command(commands: list[str]) -> int:
    """Runs the validate command"""

    try:
        for cmd in commands:
            REGISTRY.parse_command(cmd)
    except vol.Invalid as err:
        log.error(err)
        return 1

    return 0


def cmd_encode(commands: list[str]) -> int:
    """Runs the encode command"""

    try:
        for command in commands:
            cmd = REGISTRY.parse_command(command)
            signal = cmd.protocol.encode(cmd.args)

            matches = REGISTRY.decode(signal, 0.20)
            print("Sent: ", cmd.command)
            print(signal)

            matches.sort(key=lambda x: x.tolerance)
            for match in matches:
                print(
                    "Decoded: ",
                    match.protocol.to_command(match.args),
                    f"({(match.tolerance*100):.1f}% tol)",
                )
            print()
    except vol.Invalid as err:
        log.error(err)
        return 1

    return 0


def cmd_list(verbose: bool, protocols: list[str]) -> int:
    """Runs the list command"""

    if len(protocols) == 0:
        protocols = REGISTRY.list_protocols()

    for name in protocols:
        proto = REGISTRY.get_protocol(name)

        if proto is None:
            print(f"{name} Unknown protocol")
            break

        if verbose:
            print(proto.name)
            if hasattr(proto, "desc"):
                print(proto.desc)
            if hasattr(proto, "note"):
                print(proto.note)
            print(proto.get_signature())
            print()

        else:
            print(proto.get_signature())

    return 0


def run(argv: list[str]) -> int:
    """Runs the requested command"""

    if sys.version_info < (3, 8, 0):
        log.error("You need Python 3.8+ to run %s", const.PROGRAM_NAME)
        return 1

    args = parse_args(argv)

    if args.version:
        print(f"Version: {const.PROGRAM_VERSION}")

    if args.command == CMD_VALIDATE_PROTOCOL:
        return cmd_validate_protocol(args.files)

    if args.command == CMD_VALIDATE_COMMAND:
        return cmd_validate_command(args.commands)

    if args.command == CMD_ENCODE:
        return cmd_encode(args.commands)

    if args.command == CMD_LIST:
        return cmd_list(args.verbose, args.protocols)

    return 0


def main() -> int:
    """Main entry point for command line"""

    log.basicConfig(format="%(levelname)s: %(message)s")
    try:
        return run(sys.argv)
    except KeyboardInterrupt:
        return 1


if __name__ == "__main__":
    sys.exit(main())
