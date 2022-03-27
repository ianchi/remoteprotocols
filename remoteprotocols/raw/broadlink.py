"""Broadlink b64 raw format module"""

from __future__ import annotations

import base64
from typing import Any

import voluptuous as vol  # type: ignore

from remoteprotocols import validators as val
from remoteprotocols.protocol import ArgDef, DecodeMatch, ProtocolDef, SignalData

# protocol definition credit to:
# https://github.com/mjg59/python-broadlink/blob/master/protocol.md


class BroadlinkFormat(ProtocolDef):
    """Broadlink b64 raw format implementation"""

    name: str = "broadlink"
    desc: str = "Broadlink base64 raw format"
    type: str = "raw"

    args: list[ArgDef] = [
        ArgDef({"name": "b64", "desc": "Base 64 encoded data"}),
        ArgDef({"name": "frequency", "desc": "Frequency", "default": 0}),
    ]

    def parse_args(self, args: list[Any]) -> list[int]:

        vol.Length(min=1, max=2)(args)

        frequency: int = val.integer(args[1]) if len(args) == 2 else 0

        b64 = base64.b64decode(args[0])
        result: list[int] = []

        if b64[0] not in (0xB2, 0xD7, 0x26):
            raise vol.Invalid("Invalid signal type")

        # check length
        if len(b64) < 4:
            raise vol.Invalid("No header data")

        raw_len = b64[2] + (b64[3] >> 8) + 4 + 2

        if len(b64) != raw_len:
            print("inconsistent length")
            # raise vol.Invalid("Inconsistent data length")

        # Arg1: signal type
        result.append(b64[0])

        # Arg2: repeats
        result.append(b64[1])

        # Arg3... signal
        data = b64[4:]
        idx = 0
        while idx < len(data) - 2:

            if data[idx] == 0x0:  # two bytes data
                pulse = (data[idx + 1] << 8) + data[idx + 2]
                idx += 3
            else:
                pulse = data[idx]
                idx += 1

            result.append(int(pulse * 8192 / 269 + 0.5))

        # Arg N frequency
        result.append(frequency)

        return result

    def to_command(self, args: list[int]) -> str:

        command = "broadlink:"

        header: bytearray = bytearray()

        # Type
        header.append(args[0])
        # Repeat
        header.append(args[1])

        data: bytearray = bytearray()

        for pulse in args[2:-1]:
            pulse = int(abs(pulse) * 269 / 8192 + 0.5)
            if pulse > 0xFF:
                data += bytearray([0, pulse >> 8, pulse & 0xFF])
            else:
                data += bytearray([pulse])

        # Length in Little endian
        header += bytearray([len(data) & 0xFF, len(data) >> 8])

        # TODO data termination??
        data += bytearray([0, 0])

        b64 = base64.b64encode(header + data)

        command += b64.decode("UTF-8")
        if args[-1]:
            command += f":{args[-1]}"

        return command

    def encode(self, args: list[int]) -> SignalData:

        result = SignalData()

        if args[0] == 0xB2:
            result.frequency = 433 * 10**6
        elif args[0] == 0xD7:
            result.frequency = 315 * 10**6
        else:
            result.frequency = args[-1]

        result.bursts = []
        sign = 1
        for burst in args[2:-1]:
            result.bursts.append(burst * sign)
            sign *= -1

        # Repeat
        if args[1]:
            result.bursts *= 1 + args[1]

        return result

    def decode(self, signal: SignalData, _tolerance: float = 0.25) -> list[DecodeMatch]:

        match = DecodeMatch()
        match.protocol = self

        if signal.frequency < 10**6:  # Khz range --> assume IR
            match.args = [0x26, 0]
        elif signal.frequency < 370e06:  # assume 315Mhz RF
            match.args = [0xD7, 0]
        else:  # 433Mhz RF
            match.args = [0xB2, 0]

        for burst in signal.bursts:
            match.args.append(abs(burst))

        match.args.append(signal.frequency)

        return [match]
