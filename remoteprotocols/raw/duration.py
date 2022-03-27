"""Duration raw format module"""

from __future__ import annotations

from typing import Any

import voluptuous as vol  # type: ignore

from remoteprotocols import validators as val
from remoteprotocols.protocol import ArgDef, DecodeMatch, ProtocolDef, SignalData


class DurationFormat(ProtocolDef):
    """Raw durations format implementation"""

    name: str = "duration"
    desc: str = "Raw durations format"
    type: str = "raw"

    args: list[ArgDef] = [
        ArgDef({"name": "durations", "desc": "List of durations (comma separated)"}),
        ArgDef({"name": "frequency", "desc": "Frequency", "default": 0}),
    ]

    def parse_args(self, args: list[Any]) -> list[int]:

        vol.Length(min=1, max=2)(args)

        data = vol.Schema(
            [vol.All(vol.Length(min=1), val.integer, val.alternating_signs)]
        )(val.quoted_split(args[0], ","))

        frequency: int = val.integer(args[1]) if len(args) == 2 else 0
        data.append(frequency)
        return data  # type: ignore

    def to_command(self, args: list[int]) -> str:

        command = "duration:"

        for item in args[:-1]:
            command += f"{item}, "

        command = command[:-2]
        if args[-1]:
            command += f":{args[-1]}"

        return command

    def encode(self, args: list[int]) -> SignalData:

        result = SignalData()

        result.frequency = args[-1]
        result.bursts = args[:-1]

        return result

    def decode(self, signal: SignalData, _tolerance: float = 0.25) -> list[DecodeMatch]:

        match = DecodeMatch()
        match.protocol = self
        match.args = signal.bursts.copy()

        match.args.append(signal.frequency)

        return [match]
