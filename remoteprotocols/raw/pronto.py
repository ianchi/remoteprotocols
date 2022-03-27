"""Pronto raw format module"""

from __future__ import annotations

from typing import Any

import voluptuous as vol  # type: ignore

from remoteprotocols import validators as val
from remoteprotocols.protocol import ArgDef, DecodeMatch, ProtocolDef, SignalData

REFERENCE_FREQUENCY = 4145146


class ProntoFormat(ProtocolDef):
    """Pronto raw format implementation"""

    name: str = "pronto"
    desc: str = "Pronto hex raw format"
    type: str = "raw"

    args: list[ArgDef] = [
        ArgDef({"name": "data", "desc": "Data in hex codes space separated"}),
        ArgDef({"name": "frequency", "desc": "Frequency", "default": 0}),
    ]

    def parse_args(self, args: list[Any]) -> list[int]:

        if len(args) != 1:
            vol.Invalid(f"Expected one argument, got {len(args)}")

        data = val.quoted_split(args[0], " ")
        data = vol.Schema([vol.All(vol.Length(min=4, max=4), val.hex_string)])(data)

        return data  # type: ignore

    def to_command(self, args: list[int]) -> str:

        command = "pronto:"

        for item in args:
            command += f"{item:04X} "

        return command.strip()

    def encode(self, args: list[int]) -> SignalData:

        result = SignalData()

        # Learned code, raw signal with modulation
        if args[0] == 0:
            result.frequency = (
                int(REFERENCE_FREQUENCY / args[1] + 0.5) if args[1] else 0
            )
        # Learned code, non-modulated raw signal
        elif args[0] == 0x0100:
            result.frequency = 0
        else:
            raise Exception(f"Unsupported Pronto signal type 0x{args[0]:X}")

        intro_pairs = args[2]
        repeat_pairs = args[3]

        if len(args) != 4 + intro_pairs * 2 + repeat_pairs * 2:
            # inconsistent length
            raise Exception(
                f"Inconsistent length. Expected {4 + intro_pairs *2 + repeat_pairs *2} but got {len(args)}"
            )

        sign = 1
        base = int(10**6 * args[1] / REFERENCE_FREQUENCY + 0.5)
        for pulse in args[4:]:
            result.bursts.append(pulse * base * sign)
            sign *= -1

        return result

    def decode(self, signal: SignalData, _tolerance: float = 0.25) -> list[DecodeMatch]:

        match = DecodeMatch()
        match.protocol = self
        match.args = [0, 0, 0, 0]

        if signal.frequency:
            match.args[0] = 0
            match.args[1] = int(REFERENCE_FREQUENCY / signal.frequency + 0.5)
        else:
            match.args[0] = 0x0100
            match.args[1] = REFERENCE_FREQUENCY  # TODO: check valid value

        # cannot separate between intro and repeat, put everything as intro
        # TODO: encode repeat position in signal??

        if not signal.bursts:
            return []

        sign = 1
        match.args[2] = int(len(signal.bursts) / 2)
        match.args[3] = len(signal.bursts) % 2

        base = int(10**6 * match.args[1] / REFERENCE_FREQUENCY + 0.5)

        for pulse in signal.bursts:
            pulse = pulse * sign
            if pulse < 0:
                return []

            match.args.append(int(pulse / base + 0.5))
            sign *= -1

        # if it ends High, add a minimum pause
        # TODO: find a better logic that a double time
        if sign < 0:
            match.args.append(match.args[-1] * 2)

        return [match]
