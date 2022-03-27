"""Main program for command line utility"""

from __future__ import annotations

import argparse
import logging as log
import sys

import voluptuous as vol  # type: ignore

from remoteprotocols import __version__
from remoteprotocols.protocol import ProtocolDef
from remoteprotocols.registry import ProtocolRegistry
from remoteprotocols.validators import BITS_VALUES

CMD_VALIDATE_PROTOCOL = "validate-protocol"
CMD_VALIDATE_COMMAND = "validate-command"
CMD_ENCODE = "encode"
CMD_LIST = "list"
CMD_CONVERT = "convert"

REGISTRY = ProtocolRegistry()

PROGRAM_NAME = "remoteprotocols"


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Converts command line arguments in an object"""

    options_parser = argparse.ArgumentParser(add_help=False)
    options_parser.add_argument(
        "-v", "--version", help="Show version information.", action="store_true"
    )
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description=f"{PROGRAM_NAME} v{__version__}",
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
        CMD_ENCODE, help="Encodes command string(s) into raw signal (durations)."
    )
    parser_config.add_argument("commands", help="Command(s) to encode.", nargs="+")

    parser_config = subparsers.add_parser(
        CMD_CONVERT, help="Converts command string(s) to other protocols."
    )
    parser_config.add_argument("commands", help="Command(s) to convert.", nargs="+")
    parser_config.add_argument(
        "-v",
        "--verbose",
        help="Show needed tolerance to convert.",
        action="store_true",
    )
    parser_config.add_argument(
        "-t",
        "--tolerance",
        help="Use specific max tolerance in convertion.",
        nargs=1,
    )
    parser_config.add_argument(
        "-p",
        "--protocols",
        help="Only convert to specified protocols, if applicable.",
        nargs="+",
    )

    parser_config = subparsers.add_parser(CMD_LIST, help="List supported protocols.")
    parser_config.add_argument(
        "-v",
        "--verbose",
        help="Include detailed description of the protocol.",
        action="store_true",
    )
    parser_config.add_argument(
        "-m",
        "--markdown",
        help="Output in markdown format",
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

            duration = REGISTRY.get_protocol("duration")
            if duration:

                match = duration.decode(signal)
                if match:
                    print(duration.to_command(match[0].args))

            else:
                print(signal)

    except vol.Invalid as err:
        log.error(err)
        return 1

    return 0


def cmd_convert(
    commands: list[str], verbose: bool, tolerance: list[str], protocols: list[str]
) -> int:
    """Runs the decode command"""

    if not tolerance:
        tol = 0.20
    else:
        tol = float(tolerance[0])
    try:
        for command in commands:
            matches = REGISTRY.convert(command, tol, protocols)
            print("Original: ", command)

            if matches:
                print("Convertions:")
                matches.sort(key=lambda x: x.tolerance)
                for match in matches:
                    if verbose:
                        print(
                            match.protocol.to_command(match.args),
                            f"({(match.tolerance*100):.1f}% tol)",
                        )
                    else:
                        print(match.protocol.to_command(match.args))
            else:
                print("No match")
            print()
    except vol.Invalid as err:
        log.error(err)
        return 1

    return 0


# pylint: disable=too-many-branches
def cmd_list(verbose: bool, protocols: list[str], markdown: bool = False) -> int:
    """Runs the list command"""

    if len(protocols) == 0:
        protocols = REGISTRY.list_protocols()

    if markdown:
        if verbose:
            print("## Protocols details\n")
        else:
            print("## List of supported protocols\n")
            print("| Protocol | Signature | Type | Description |")
            print("| --- | --- | --- | --- |")

    for name in protocols:
        proto = REGISTRY.get_protocol(name)

        if proto is None:
            if markdown:
                print(f"| {name} | | Unk | Unknown protocol |")
            else:
                print(f"{name} Unknown protocol")
            break

        signature = proto.get_signature()
        if markdown:
            signature = signature.replace("<", "&lt;").replace(">", "&gt;")

        if verbose:

            if markdown:
                print(proto_help_md(proto))

            else:
                print(proto.name)
                if hasattr(proto, "desc"):
                    print(proto.desc)
                if hasattr(proto, "note"):
                    print(proto.note)
                print(proto.get_signature())
                print()

        else:
            if markdown:
                print(
                    f"| [{name}](#{name}) | {signature} | {proto.type if hasattr(proto,'type') else '??'} | {proto.desc} |"
                )
            else:
                print(signature)

    return 0


def proto_help_md(proto: ProtocolDef) -> str:
    """Generets help for protocol in Markdown format"""

    signature = proto.get_signature()
    signature = signature.replace("<", "&lt;").replace(">", "&gt;")
    name = proto.name

    output = ""

    output += f"\n### **{name}**\n"
    output += f"{proto.desc}\n"
    output += f"\n*Type:* {proto.type if hasattr(proto,'type') else '??'}\n"
    output += f"\n*Signature:* {signature}\n"
    output += "\n*Arguments:*\n"
    for arg in proto.args:
        output += f"- *{arg.name}*: {arg.desc}\n"
        if arg.default is not None:
            output += f"\n   optional. Default: {arg.default}\n"
        if hasattr(arg, "max"):
            max_str = str(arg.max)
            for key, val in BITS_VALUES.items():
                if arg.max == val:
                    max_str = key
                    break

            output += f"\n   range: {arg.min}-{max_str}\n"
        if hasattr(arg, "values") and arg.values:
            output += f"\n   values: {arg.values}\n"
    if hasattr(proto, "note"):
        output += f"\n*Notes:*\n\n{proto.note}\n"

    if hasattr(proto, "link") and proto.link:
        output += "\n*Links:*\n"
        for link in proto.link:
            output += f"\n- [{link}]({link})\n"

    return output


def run(argv: list[str]) -> int:
    """Runs the requested command"""

    if sys.version_info < (3, 8, 0):
        log.error("You need Python 3.8+ to run %s", PROGRAM_NAME)
        return 1

    args = parse_args(argv)

    if args.version:
        print(f"Version: {__version__}")

    if args.command == CMD_VALIDATE_PROTOCOL:
        return cmd_validate_protocol(args.files)

    if args.command == CMD_VALIDATE_COMMAND:
        return cmd_validate_command(args.commands)

    if args.command == CMD_ENCODE:
        return cmd_encode(args.commands)

    if args.command == CMD_CONVERT:
        return cmd_convert(args.commands, args.verbose, args.tolerance, args.protocols)

    if args.command == CMD_LIST:
        return cmd_list(args.verbose, args.protocols, args.markdown)

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
