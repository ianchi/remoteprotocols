# Functions to work with command strings
#
from typing import Optional

import voluptuous as vol  # type: ignore

import remoteprotocols.validators as val
from remoteprotocols.protocol.definition import ProtocolDef, ProtocolRegistry


class RemoteCommand:

    name: str
    args: list[int]
    command: str

    protocol: Optional[ProtocolDef]

    def __init__(self, command: str) -> None:

        if not isinstance(command, str):
            raise vol.Invalid(f"Command must be a string, got {command}")

        self.command = command
        command_list = val.quoted_split(command, ":")

        if len(command_list) == 0:
            raise vol.Invalid("Missing protocol in command")

        try:
            self.name = val.string_strict(command_list[0]).lower()
            self.args = vol.Schema([val.integer])(command_list[1:])
        except vol.Invalid as err:
            raise vol.Invalid(f"Invalid command '{self.command}'. {err}")

    def validate(self, registry: ProtocolRegistry) -> None:

        self.protocol = registry.get_protocol(self.name)

        if self.protocol is None:
            raise Exception(f"Unknown Protocol '{self.name}'")
        try:
            self.protocol.validate_command(self.args)
        except vol.Invalid as err:
            raise vol.Invalid(
                f"Invalid command '{self.command}'. {err}\nExpected '{self.protocol.get_signature()}'"
            )


def validate_command(_command: str) -> None:
    """Validates a command string according to proto definition
    and returns a command object with the parsed protocol & arguments (including any defaults)
    """
