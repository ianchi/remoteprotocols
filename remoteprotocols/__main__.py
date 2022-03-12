import argparse
import codecs
import logging as log
import pathlib
import sys
from typing import Any

import voluptuous as vol  # type: ignore
import yaml

from remoteprotocols import const, encode
from remoteprotocols.command import RemoteCommand
from remoteprotocols.decoder import decode
from remoteprotocols.protocol import validate_protocols
from remoteprotocols.protocol.definition import ProtocolRegistry

CMD_VALIDATE_PROTOCOL = "validate-protocol"
CMD_VALIDATE_COMMAND = "validate-command"
CMD_ENCODE = "encode"
CMD_LIST = "list"

REGISTRY = ProtocolRegistry()


def parse_args(argv: list[str]) -> argparse.Namespace:
    options_parser = argparse.ArgumentParser(add_help=False)
    options_parser.add_argument(
        "-v", "--version", help="Show version information.", action="store_true"
    )
    parser = argparse.ArgumentParser(
        description=f"{const.program} v{const.version}", parents=[options_parser]
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


def read_yaml(file: str) -> Any:
    path = pathlib.Path(file).resolve()

    try:
        with codecs.open(path.as_posix(), "r", encoding="utf-8") as f_handle:
            data = yaml.safe_load(f_handle)
    except yaml.MarkedYAMLError as err:
        mark = err.problem_mark
        if mark:
            log.error(
                "Error parsing yaml file at [%i:%i]: %s",
                mark.line + 1,
                mark.column + 1,
                err.problem,
            )
        else:
            log.error(err)
        return None
    except yaml.YAMLError as err:
        log.error(err)
        return None

    return data


def load_protocols() -> None:
    path = pathlib.Path(__file__).parent / const.PROTOCOLS_YAML
    proto = read_yaml(path.as_posix())
    proto = validate_protocols(proto)

    REGISTRY.add_protocols(proto)


def cmd_validate_protocol(files: list[str]) -> int:

    for file in files:

        data = read_yaml(file)

        if data is None:
            return 1
        try:
            proto = validate_protocols(data)
            print(proto)

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

    try:
        for c in commands:
            cmd = RemoteCommand(c)
            cmd.validate(REGISTRY)
    except vol.Invalid as err:
        log.error(err)
        return 1

    return 0


def cmd_encode(commands: list[str]) -> int:

    try:
        for c in commands:
            cmd = RemoteCommand(c)
            cmd.validate(REGISTRY)
            signal = encode(cmd.protocol, cmd.args)

            match = decode(signal, REGISTRY, 0.20)
            print(cmd.command)
            print(signal)

            for m in match:
                print(m.protocol.to_command(m.args))

    except vol.Invalid as err:
        log.error(err)
        return 1

    return 0


def cmd_list(verbose: bool, protocols: list[str]) -> int:

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

    if sys.version_info < (3, 8, 0):
        log.error("You need Python 3.8+ to run %s", const.program)
        return 1

    args = parse_args(argv)

    if args.version:
        print(f"Version: {const.version}")

    if args.command == CMD_VALIDATE_PROTOCOL:
        return cmd_validate_protocol(args.files)

    if args.command == CMD_VALIDATE_COMMAND:
        load_protocols()
        return cmd_validate_command(args.commands)

    if args.command == CMD_ENCODE:
        load_protocols()
        return cmd_encode(args.commands)

    if args.command == CMD_LIST:
        load_protocols()
        return cmd_list(args.verbose, args.protocols)

    return 0


def main() -> int:
    log.basicConfig(format="%(levelname)s: %(message)s")
    try:
        return run(sys.argv)
    except KeyboardInterrupt:
        return 1


if __name__ == "__main__":
    sys.exit(main())
