"""Base Protocol Definition Classes, shared between encoded protocols and raw formats."""

from __future__ import annotations

from typing import Any


class ArgDef:
    """Definition of a single argument."""

    name: str
    desc: str | None = None
    default: int | None = None
    example: int | None = None
    print: str

    min: int = 0
    max: int
    values: list[int] | None = None

    def __init__(self, value: dict[(str, Any)]) -> None:
        self.values = []
        for key, data in value.items():
            setattr(self, key, data)

    def __repr__(self) -> str:
        return self.__dict__.__str__()


class SignalData:
    """Raw burst information as durations."""

    frequency: int = 0
    bursts: list[int]

    def __repr__(self) -> str:
        return self.__dict__.__str__()


class DecodeMatch:
    """Single decoding match, with args and un-decoded masks."""

    protocol: ProtocolDef
    args: list[int]
    missing_bits: list[int]
    uniquematch: bool = True
    toggle_bit: int
    tolerance: float = 0

    def __repr__(self) -> str:
        return self.__dict__.__str__()


class ProtocolDef:
    """Base class for all protocols. Both encoded and raw formats."""

    name: str
    type: str
    desc: str
    note: str
    link: list[str]

    args: list[ArgDef]

    def __repr__(self) -> str:
        return self.__dict__.__str__()

    def get_signature(self) -> str:
        """Get help string with the signature to use to send a command."""

        signature = [self.name]

        for arg in self.args:
            if arg.default is not None:
                signature.append(f"<{arg.name}?={arg.default}>")
            else:
                signature.append(f"<{arg.name}>")

        return ":".join(signature)

    def parse_args(self, args: list[str]) -> list[int]:
        """Validate arg list as strings, and converts it to final list of numbers to use in protocol."""

    def to_command(self, args: list[int]) -> str:
        """Convert list of arguments as a command string."""

    def encode(self, args: list[int]) -> SignalData:
        """Encode arguments into a raw signal."""

    def decode(self, signal: SignalData, tolerance: float = 0.25) -> list[DecodeMatch]:
        """Decode signal into protocol arguments. Empty list if no match."""


class RemoteCommand:
    """Class to hold a parsed command."""

    name: str
    args: list[int]
    command: str
    protocol: ProtocolDef

    def __repr__(self) -> str:
        return self.command
