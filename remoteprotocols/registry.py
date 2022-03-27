"""Module to handle registry of all protocols"""

from __future__ import annotations

import codecs
import pathlib
from typing import Any, Optional

import voluptuous as vol  # type:ignore
import yaml

import remoteprotocols.validators as val
from remoteprotocols.protocol import DecodeMatch, ProtocolDef, RemoteCommand, SignalData
from remoteprotocols.raw.broadlink import BroadlinkFormat
from remoteprotocols.raw.duration import DurationFormat
from remoteprotocols.raw.miio import MiioFormat
from remoteprotocols.raw.pronto import ProntoFormat

PROTOCOLS_YAML = "codecs/protocols.yaml"


class ProtocolRegistry:
    """Registry to store all available protocols.
    Dispatches calls to respective protocol.
    """

    # Use class attribute, to be shared as singleton instance
    protocols: dict[(str, ProtocolDef)] = {}

    def __init__(self, load_builtin: bool = True) -> None:
        if load_builtin:
            path = pathlib.Path(__file__).parent / PROTOCOLS_YAML
            self.load(path.as_posix())
            self.add_protocol(ProntoFormat())
            self.add_protocol(DurationFormat())
            self.add_protocol(BroadlinkFormat())
            self.add_protocol(MiioFormat())

    def add_protocols_def(self, definition: dict[(str, Any)]) -> None:
        """Validates a dict of encoded protocols definitions and converts them into CodecDef objects
        and updates the registry"""

        from remoteprotocols.codecs import schema1

        protocols = schema1.PROTOCOLS_DEF_SCHEMA(definition)

        self.protocols.update(protocols)

    def add_protocol(self, protocol: ProtocolDef) -> None:
        """Adds a single protocol to the registry"""
        self.protocols[protocol.name] = protocol

    def load(self, file: str) -> None:
        """Reads a yaml file and adds it to the registry"""

        path = pathlib.Path(file).resolve()

        try:
            with codecs.open(path.as_posix(), "r", encoding="utf-8") as f_handle:
                data = yaml.safe_load(f_handle)
        except yaml.MarkedYAMLError as err:
            mark = err.problem_mark
            if mark:
                raise vol.Invalid(
                    f"Error parsing yaml file {file}[{mark.line + 1}:{mark.column + 1}]: {err.problem}"
                )
            raise err

        self.add_protocols_def(data)

    def get_protocol(self, name: str) -> Optional[ProtocolDef]:
        """Returns a protocol by name"""
        return self.protocols[name] if name in self.protocols else None

    def list_protocols(self) -> list[str]:
        """List all supported protocols in alphabetical order"""

        protocols = list(self.protocols)
        protocols.sort()
        return protocols

    def parse_command(self, command: str) -> RemoteCommand:
        """Parses and validates a command string into a RemoteCommand object"""
        cmd = RemoteCommand()

        if not isinstance(command, str):
            raise vol.Invalid(f"Command must be a string, got {command}")

        cmd.command = command
        command_list = val.quoted_split(command, ":")

        if len(command_list) == 0:
            raise vol.Invalid("Missing protocol in command")

        cmd.name = val.string_strict(command_list[0]).lower()
        args = command_list[1:]

        proto = self.get_protocol(cmd.name)

        if proto is None:
            raise Exception(f"Unknown Protocol '{cmd.name}'")
        try:
            cmd.protocol = proto
            cmd.args = cmd.protocol.parse_args(args)
        except vol.Invalid as err:
            raise vol.Invalid(
                f"Invalid command '{command}'. {err}\nExpected '{cmd.protocol.get_signature()}'"
            )

        return cmd

    def decode(
        self,
        signal: SignalData,
        tolerance: float = 0.20,
        protocols: Optional[list[str]] = None,
    ) -> list[DecodeMatch]:
        """Decodes a signal and returns a list of all matching protocols and corresponding decoded arguments.
        It decodes into all known protocols or a filtered subset
        """

        decoded: list[DecodeMatch] = []

        for proto in self.protocols.values():
            if not protocols or protocols.count(proto.name):
                decoded += proto.decode(signal, tolerance)

        return decoded

    def convert(
        self,
        command: str,
        tolerance: float = 0.20,
        protocols: Optional[list[str]] = None,
    ) -> list[DecodeMatch]:
        """Converts a given command into other protocols (all or filtered)"""

        cmd = self.parse_command(command)
        signal = cmd.protocol.encode(cmd.args)

        matches = self.decode(signal, tolerance, protocols)

        return matches
